/*
 * Sensor Node Application for Contiki-NG
 * Integrates with SDN-WISE Agent
 */

#include "contiki.h"
#include "dev/leds.h"
#include "net/ipv6/simple-udp.h"
#include "net/ipv6/uip.h"
#include "net/routing/routing.h"
#include "sys/log.h"
#include <stdio.h>
#include <stdlib.h>


#define LOG_MODULE "SENSOR"
#define LOG_LEVEL LOG_LEVEL_INFO

#define UDP_CLIENT_PORT 8765
#define UDP_SERVER_PORT 5678

// Simulated sensor data
static int temperature = 20;
static int humidity = 50;
static int light = 100;

static struct simple_udp_connection udp_conn;

/*---------------------------------------------------------------------------*/
static void udp_rx_callback(struct simple_udp_connection *c,
                            const uip_ipaddr_t *sender_addr,
                            uint16_t sender_port,
                            const uip_ipaddr_t *receiver_addr,
                            uint16_t receiver_port, const uint8_t *data,
                            uint16_t datalen) {
  LOG_INFO("Received command: %.*s\n", datalen, (char *)data);

  // Toggle LED on command
  leds_toggle(LEDS_GREEN);
}

/*---------------------------------------------------------------------------*/
static void send_sensor_data(void) {
  if (NETSTACK_ROUTING.node_is_root()) {
    return; // Root doesn't send sensor data
  }

  uip_ipaddr_t dest_ipaddr;

  // Get root address (border router)
  if (!NETSTACK_ROUTING.get_root_ipaddr(&dest_ipaddr)) {
    LOG_WARN("No route to root yet\n");
    return;
  }

  // Simulate sensor readings with some variation
  temperature = 20 + (rand() % 10);
  humidity = 50 + (rand() % 20);
  light = 100 + (rand() % 50);

  // Build sensor data packet
  char buffer[64];
  snprintf(buffer, sizeof(buffer), "SENSOR:temp=%d,hum=%d,light=%d",
           temperature, humidity, light);

  // Send to border router
  simple_udp_sendto(&udp_conn, buffer, strlen(buffer), &dest_ipaddr);

  LOG_INFO("Sent: %s\n", buffer);

  // Blink LED (only on platforms that support clock_delay_usec)
  leds_on(LEDS_BLUE);
#ifndef PLATFORM_NATIVE
  clock_delay_usec(50000);
#endif
  leds_off(LEDS_BLUE);
}

/*---------------------------------------------------------------------------*/
PROCESS(sensor_node_process, "Sensor Node");
AUTOSTART_PROCESSES(&sensor_node_process);

PROCESS_THREAD(sensor_node_process, ev, data) {
  static struct etimer periodic_timer;
  static struct etimer startup_timer;

  PROCESS_BEGIN();

  LOG_INFO("Sensor Node Application started\n");

  // Get node address
  linkaddr_t *addr = &linkaddr_node_addr;
  uint16_t node_id = (addr->u8[6] << 8) | addr->u8[7];
  LOG_INFO("Node ID: %u\n", node_id);

  // Initialize LEDs
  leds_off(LEDS_ALL);

  // Register UDP connection
  simple_udp_register(&udp_conn, UDP_CLIENT_PORT, NULL, UDP_SERVER_PORT,
                      udp_rx_callback);

  // Wait for network to form (RPL)
  etimer_set(&startup_timer, CLOCK_SECOND * 15);
  PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&startup_timer));

  // Check node role
  if (NETSTACK_ROUTING.node_is_root()) {
    LOG_INFO("I am the ROOT/SINK - not sending sensor data\n");
    leds_on(LEDS_RED); // Red LED for root

    // Root just listens
    while (1) {
      PROCESS_WAIT_EVENT();
    }
  } else {
    LOG_INFO("I am a SENSOR - starting periodic sensing\n");
    leds_on(LEDS_GREEN); // Green LED for sensors

    // Periodic timer for sensor readings
    etimer_set(&periodic_timer, CLOCK_SECOND * 10);

    while (1) {
      PROCESS_WAIT_EVENT_UNTIL(etimer_expired(&periodic_timer));

      // Send sensor data
      send_sensor_data();

      // Reset timer (10 seconds)
      etimer_reset(&periodic_timer);
    }
  }

  PROCESS_END();
}
