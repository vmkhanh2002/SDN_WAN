/*
 * SDN-WISE Agent for Contiki-NG
 * Implements SDN-WISE protocol for wireless sensor networks
 */

#include "contiki.h"
#include "net/ipv6/simple-udp.h"
#include "net/ipv6/uip.h"
#include "net/routing/routing.h"
#include "sys/log.h"
#include <string.h>

#define LOG_MODULE "SDN-WISE"
#define LOG_LEVEL LOG_LEVEL_INFO

// SDN-WISE packet types
#define WISE_TYPE_DATA 0x01
#define WISE_TYPE_BEACON 0x02
#define WISE_TYPE_REPORT 0x03
#define WISE_TYPE_REQUEST 0x04
#define WISE_TYPE_RESPONSE 0x05
#define WISE_TYPE_OPEN_PATH 0x06
#define WISE_TYPE_CONFIG 0x10
#define WISE_TYPE_REG_PROXY 0x11
#define WISE_TYPE_FLOW_RULE 0x12

// Ports
#define UDP_CLIENT_PORT 8765
#define UDP_SERVER_PORT 5678

// Flow table configuration
#define MAX_FLOW_RULES 10

// Flow rule structure
typedef struct {
  uint8_t active;
  uint16_t src_addr;
  uint16_t dst_addr;
  uint8_t action; // 0: DROP, 1: FORWARD, 2: ASK_CONTROLLER
  uint16_t next_hop;
  uint32_t packet_count;
} flow_rule_t;

// Global flow table
static flow_rule_t flow_table[MAX_FLOW_RULES];
static uint8_t flow_count = 0;

// UDP connection
static struct simple_udp_connection udp_conn;

// Node statistics
static struct {
  uint32_t packets_sent;
  uint32_t packets_received;
  uint32_t packets_forwarded;
  uint32_t packets_dropped;
} stats;

/*---------------------------------------------------------------------------*/
/* Flow Table Management */
/*---------------------------------------------------------------------------*/

static int flow_table_add(uint16_t src, uint16_t dst, uint8_t action,
                          uint16_t next_hop) {
  if (flow_count >= MAX_FLOW_RULES) {
    LOG_WARN("Flow table full!\n");
    return -1;
  }

  flow_table[flow_count].active = 1;
  flow_table[flow_count].src_addr = src;
  flow_table[flow_count].dst_addr = dst;
  flow_table[flow_count].action = action;
  flow_table[flow_count].next_hop = next_hop;
  flow_table[flow_count].packet_count = 0;

  LOG_INFO("Flow added: %u->%u action=%u next=%u\n", src, dst, action,
           next_hop);

  flow_count++;
  return 0;
}

static flow_rule_t *flow_table_lookup(uint16_t src, uint16_t dst) {
  for (uint8_t i = 0; i < flow_count; i++) {
    if (flow_table[i].active && flow_table[i].src_addr == src &&
        flow_table[i].dst_addr == dst) {
      return &flow_table[i];
    }
  }
  return NULL;
}

static void flow_table_clear(void) {
  memset(flow_table, 0, sizeof(flow_table));
  flow_count = 0;
  LOG_INFO("Flow table cleared\n");
}

/*---------------------------------------------------------------------------*/
/* Packet Processing */
/*---------------------------------------------------------------------------*/

static void process_wise_packet(const uint8_t *data, uint16_t len) {
  uint8_t packet_len;
  uint8_t packet_type;
  uint16_t dst_addr;
  uint16_t src_addr;
  uint8_t ttl;
  flow_rule_t *rule;
  uint8_t action;    /* C89: declare at function start */
  uint16_t next_hop; /* C89: declare at function start */

  if (len < 7) {
    LOG_WARN("Packet too short: %hu bytes\n", len);
    return;
  }

  packet_len = data[0];
  (void)packet_len; /* Suppress unused variable warning */
  packet_type = data[1];
  dst_addr = (data[2] << 8) | data[3];
  src_addr = (data[4] << 8) | data[5];
  ttl = data[6];

  LOG_INFO("RX: type=%hhu src=%hu dst=%hu ttl=%hhu\n", packet_type, src_addr,
           dst_addr, ttl);

  stats.packets_received++;

  switch (packet_type) {
  case WISE_TYPE_FLOW_RULE:
    if (len >= 14) {
      action = data[7];
      next_hop = (data[8] << 8) | data[9];
      flow_table_add(src_addr, dst_addr, action, next_hop);
    }
    break;

  case WISE_TYPE_DATA:
    // Forward data packet based on flow table
    rule = flow_table_lookup(src_addr, dst_addr);
    if (rule != NULL) {
      rule->packet_count++;
      stats.packets_forwarded++;
      LOG_INFO("Forwarding to next_hop=%hu\n", rule->next_hop);
    } else {
      stats.packets_dropped++;
      LOG_WARN("No flow rule, asking controller\n");
    }
    break;

  case WISE_TYPE_CONFIG:
    LOG_INFO("Configuration packet received\n");
    break;

  default:
    LOG_WARN("Unknown packet type: %u\n", packet_type);
    break;
  }
}

/*---------------------------------------------------------------------------*/
/* UDP Callback */
/*---------------------------------------------------------------------------*/

static void udp_rx_callback(struct simple_udp_connection *c,
                            const uip_ipaddr_t *sender_addr,
                            uint16_t sender_port,
                            const uip_ipaddr_t *receiver_addr,
                            uint16_t receiver_port, const uint8_t *data,
                            uint16_t datalen) {
  LOG_INFO("UDP RX from ");
  LOG_INFO_6ADDR(sender_addr);
  LOG_INFO_(" (%u bytes)\n", datalen);

  process_wise_packet(data, datalen);
}

/*---------------------------------------------------------------------------*/
/* Send Functions */
/*---------------------------------------------------------------------------*/

static void send_report_to_controller(void) {
  if (NETSTACK_ROUTING.node_is_root()) {
    return; // Root doesn't send reports
  }

  uip_ipaddr_t dest_ipaddr;
  NETSTACK_ROUTING.get_root_ipaddr(&dest_ipaddr);

  // Build WISE report packet
  uint8_t buffer[32];
  buffer[0] = 20; // length
  buffer[1] = WISE_TYPE_REPORT;

  // Source address (this node)
  linkaddr_t *addr = &linkaddr_node_addr;
  uint16_t node_id = (addr->u8[6] << 8) | addr->u8[7];
  buffer[2] = (node_id >> 8) & 0xFF;
  buffer[3] = node_id & 0xFF;

  // Statistics
  buffer[7] = (stats.packets_sent >> 24) & 0xFF;
  buffer[8] = (stats.packets_sent >> 16) & 0xFF;
  buffer[9] = (stats.packets_sent >> 8) & 0xFF;
  buffer[10] = stats.packets_sent & 0xFF;

  simple_udp_sendto(&udp_conn, buffer, 20, &dest_ipaddr);

  LOG_INFO("Report sent: pkts_sent=%lu pkts_rx=%lu\n",
           (unsigned long)stats.packets_sent,
           (unsigned long)stats.packets_received);

  stats.packets_sent++;
}

/*---------------------------------------------------------------------------*/
/* Process */
/*---------------------------------------------------------------------------*/

PROCESS(sdn_wise_agent_process, "SDN-WISE Agent");
AUTOSTART_PROCESSES(&sdn_wise_agent_process);

PROCESS_THREAD(sdn_wise_agent_process, ev, data) {
  static struct etimer periodic_timer;
  static struct etimer stats_timer;

  PROCESS_BEGIN();

  LOG_INFO("SDN-WISE Agent started\n");

  // Initialize statistics
  memset(&stats, 0, sizeof(stats));

  // Initialize flow table
  flow_table_clear();

  // Get node ID
  linkaddr_t *addr = &linkaddr_node_addr;
  uint16_t node_id = (addr->u8[6] << 8) | addr->u8[7];
  LOG_INFO("Node ID: %u (0x%04x)\n", node_id, node_id);

  // Register UDP connection
  simple_udp_register(&udp_conn, UDP_CLIENT_PORT, NULL, UDP_SERVER_PORT,
                      udp_rx_callback);

  LOG_INFO("Listening on UDP port %u\n", UDP_CLIENT_PORT);

  // Wait for network to form
  etimer_set(&periodic_timer, CLOCK_SECOND * 10);
  PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&periodic_timer));

  // Check if this is the border router (root)
  if (NETSTACK_ROUTING.node_is_root()) {
    LOG_INFO("I am the BORDER ROUTER (SINK)\n");
  } else {
    LOG_INFO("I am a SENSOR NODE\n");
  }

  // Periodic timer for reports
  etimer_set(&periodic_timer, CLOCK_SECOND * 30);

  // Stats timer
  etimer_set(&stats_timer, CLOCK_SECOND * 60);

  while (1) {
    PROCESS_WAIT_EVENT();

    if (etimer_expired(&periodic_timer)) {
      // Send periodic report to controller
      send_report_to_controller();
      etimer_reset(&periodic_timer);
    }

    if (etimer_expired(&stats_timer)) {
      // Print statistics
      LOG_INFO("=== Stats ===\n");
      LOG_INFO("TX: %lu, RX: %lu, FWD: %lu, DROP: %lu\n",
               (unsigned long)stats.packets_sent,
               (unsigned long)stats.packets_received,
               (unsigned long)stats.packets_forwarded,
               (unsigned long)stats.packets_dropped);
      LOG_INFO("Flows: %u/%u\n", flow_count, MAX_FLOW_RULES);
      etimer_reset(&stats_timer);
    }
  }

  PROCESS_END();
}
