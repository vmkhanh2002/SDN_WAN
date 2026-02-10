package org.onosproject.wisesdn;

import org.onosproject.net.packet.PacketContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * SDN-WISE Controller
 * Handles WSN protocol logic and packet processing
 */
public class WiseController {

    private static final Logger log = LoggerFactory.getLogger(WiseController.class);

    private final FlowTableManager flowManager;
    private final TopologyManager topologyManager;

    // Statistics
    private final Map<Integer, NodeStats> nodeStats = new ConcurrentHashMap<>();

    // Security & Compliance
    private final Map<Integer, Boolean> patientConsentMap = new ConcurrentHashMap<>();
    private final Map<Integer, String> deviceIdentityMap = new ConcurrentHashMap<>();

    // Policy Constants
    public static final String ACTION_FORWARD = "FORWARD";
    public static final String ACTION_ACCESS_DATA = "ACCESS_DATA";

    public WiseController(FlowTableManager flowManager, TopologyManager topologyManager) {
        this.flowManager = flowManager;
        this.topologyManager = topologyManager;
    }

    /**
     * Handle incoming SDN-WISE packet
     */
    public void handlePacket(WisePacket packet, PacketContext context) {
        log.debug("Processing packet: {}", packet);

        // Update topology
        topologyManager.updateNode(packet.getSrc(), System.currentTimeMillis());

        // Update stats
        updateStats(packet.getSrc());

        switch (packet.getTyp()) {
            case WisePacket.TYPE_DATA:
                handleDataPacket(packet, context);
                break;

            case WisePacket.TYPE_CONFIG:
                handleConfigPacket(packet, context);
                break;

            case WisePacket.TYPE_FLOW_RULE:
                handleFlowRulePacket(packet, context);
                break;

            case WisePacket.TYPE_TOPOLOGY:
                handleTopologyPacket(packet, context);
                break;

            case WisePacket.TYPE_STATS:
                handleStatsPacket(packet, context);
                break;

            default:
                log.warn("Unknown packet type: {}", packet.getTyp());
        }
    }

    /**
     * Handle data packet from sensor node
     */
    private void handleDataPacket(WisePacket packet, PacketContext context) {
        log.debug("Data packet from node {}: {} bytes",
                String.format("0x%04X", packet.getSrc()),
                packet.getPayload() != null ? packet.getPayload().length : 0);

        // Enforce Policy: Check Consent
        if (!checkPolicy(packet.getSrc(), ACTION_FORWARD)) {
            log.warn("Dropping packet from node {} due to policy violation (No Consent)",
                    String.format("0x%04X", packet.getSrc()));
            return;
        }

        // Check if there's a flow rule for this packet
        FlowRule rule = flowManager.getMatchingFlow(packet.getSrc(), packet.getDst());

        if (rule != null) {
            log.debug("Found flow rule: forward to {}", String.format("0x%04X", rule.getNextHop()));
            // Forward according to flow rule
            forwardPacket(packet, rule.getNextHop(), context);
        } else {
            log.debug("No flow rule found - sending to controller");
            // No flow rule - handle at controller
            processAtController(packet);
        }
    }

    /**
     * Handle configuration packet
     */
    private void handleConfigPacket(WisePacket packet, PacketContext context) {
        log.info("Config packet from node {}", String.format("0x%04X", packet.getSrc()));

        // Extract configuration parameters from payload
        // This would parse sensor capabilities, battery level, etc.
        topologyManager.updateNodeConfig(packet.getSrc(), packet.getPayload());
    }

    /**
     * Handle flow rule acknowledgment
     */
    private void handleFlowRulePacket(WisePacket packet, PacketContext context) {
        log.info("Flow rule ACK from node {}", String.format("0x%04X", packet.getSrc()));
        flowManager.markFlowInstalled(packet.getSrc());
    }

    /**
     * Handle topology update packet
     */
    private void handleTopologyPacket(WisePacket packet, PacketContext context) {
        log.debug("Topology update from node {}", String.format("0x%04X", packet.getSrc()));

        // Parse neighbor list from payload
        if (packet.getPayload() != null && packet.getPayload().length >= 2) {
            int numNeighbors = packet.getPayload()[0] & 0xFF;
            log.debug("Node has {} neighbors", numNeighbors);

            for (int i = 0; i < numNeighbors && (i * 2 + 2) < packet.getPayload().length; i++) {
                int neighborId = ((packet.getPayload()[i * 2 + 1] & 0xFF) << 8) |
                        (packet.getPayload()[i * 2 + 2] & 0xFF);
                topologyManager.addLink(packet.getSrc(), neighborId);
            }
        }
    }

    /**
     * Handle statistics packet
     */
    private void handleStatsPacket(WisePacket packet, PacketContext context) {
        log.debug("Stats packet from node {}", String.format("0x%04X", packet.getSrc()));

        NodeStats stats = nodeStats.computeIfAbsent(packet.getSrc(), k -> new NodeStats());

        // Parse stats from payload (battery, packet count, etc.)
        if (packet.getPayload() != null && packet.getPayload().length >= 4) {
            stats.batteryLevel = packet.getPayload()[0] & 0xFF;
            stats.packetsSent = ((packet.getPayload()[1] & 0xFF) << 8) | (packet.getPayload()[2] & 0xFF);
            stats.packetsReceived = packet.getPayload()[3] & 0xFF;
        }

        log.debug("Node stats - Battery: {}%, Sent: {}, Recv: {}",
                stats.batteryLevel, stats.packetsSent, stats.packetsReceived);
    }

    /**
     * Forward packet to next hop
     */
    private void forwardPacket(WisePacket packet, int nextHop, PacketContext context) {
        packet.setNxh(nextHop);
        packet.setTtl((byte) (packet.getTtl() - 1));

        // In a real implementation, this would send the packet
        log.debug("Forwarding packet to {}", String.format("0x%04X", nextHop));
    }

    /**
     * Process packet at controller
     */
    private void processAtController(WisePacket packet) {
        // Extract sensor data from payload
        log.info("Processing sensor data at controller from node {}",
                String.format("0x%04X", packet.getSrc()));

        // This could trigger analytics, storage, or other actions
    }

    /**
     * Update packet statistics for a node
     */
    private void updateStats(int nodeId) {
        NodeStats stats = nodeStats.computeIfAbsent(nodeId, k -> new NodeStats());
        stats.lastSeen = System.currentTimeMillis();
        stats.packetsReceived++;
    }

    /**
     * Get statistics for a node
     */
    public NodeStats getNodeStats(int nodeId) {
        return nodeStats.get(nodeId);
    }

    /**
     * Node statistics class
     */
    public static class NodeStats {
        public long lastSeen;
        public int batteryLevel = 100;
        public int packetsSent;
        public int packetsReceived;

        public String toString() {
            return String.format("NodeStats{battery=%d%%, sent=%d, recv=%d, lastSeen=%d}",
                    batteryLevel, packetsSent, packetsReceived, lastSeen);
        }
    }

    /**
     * Set patient consent for a specific node (Compliance)
     */
    public void setPatientConsent(int nodeId, boolean hasConsent) {
        patientConsentMap.put(nodeId, hasConsent);
        log.info("Updated consent for node {}: {}", String.format("0x%04X", nodeId), hasConsent);
    }

    /**
     * Get patient consent status
     */
    public boolean getPatientConsent(int nodeId) {
        return patientConsentMap.getOrDefault(nodeId, false); // Default to FALSE (Deny)
    }

    /**
     * Check compliance policy
     */
    public boolean checkPolicy(int nodeId, String action) {
        if (ACTION_ACCESS_DATA.equals(action) || ACTION_FORWARD.equals(action)) {
            // Require consent for data access/forwarding
            boolean consent = getPatientConsent(nodeId);
            if (!consent) {
                log.warn("POLICY VIOLATION: Node {} attempted {} without patient consent",
                        String.format("0x%04X", nodeId), action);
                return false;
            }
        }
        return true;
    }

    /**
     * Register device identity
     */
    public void registerDevice(int nodeId, String identity) {
        deviceIdentityMap.put(nodeId, identity);
        log.info("Registered device identity: {} -> {}", String.format("0x%04X", nodeId), identity);
    }
}
