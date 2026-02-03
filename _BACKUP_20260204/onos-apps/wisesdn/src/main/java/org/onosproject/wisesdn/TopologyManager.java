package org.onosproject.wisesdn;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * Topology Manager for WSN
 * Tracks sensor nodes and network links
 */
public class TopologyManager {

    private static final Logger log = LoggerFactory.getLogger(TopologyManager.class);

    // Sensor nodes: nodeId -> WiseNode
    private final Map<Integer, WiseNode> nodes = new ConcurrentHashMap<>();

    // Network links: nodeId -> set of neighbor IDs
    private final Map<Integer, Set<Integer>> links = new ConcurrentHashMap<>();

    // Node timeout (30 seconds)
    private static final long NODE_TIMEOUT_MS = 30000;

    /**
     * Update node status
     */
    public void updateNode(int nodeId, long timestamp) {
        WiseNode node = nodes.computeIfAbsent(nodeId, k -> new WiseNode(nodeId));
        node.lastSeen = timestamp;
        node.active = true;

        log.debug("Updated node {}: lastSeen={}", String.format("0x%04X", nodeId), timestamp);
    }

    /**
     * Update node configuration
     */
    public void updateNodeConfig(int nodeId, byte[] config) {
        WiseNode node = nodes.computeIfAbsent(nodeId, k -> new WiseNode(nodeId));

        // Parse config (simplified)
        if (config != null && config.length >= 2) {
            node.nodeType = config[0];
            node.batteryLevel = config[1] & 0xFF;
            log.debug("Node {} config updated: type={}, battery={}%",
                    String.format("0x%04X", nodeId), node.nodeType, node.batteryLevel);
        }
    }

    /**
     * Add link between nodes
     */
    public void addLink(int srcNode, int dstNode) {
        links.computeIfAbsent(srcNode, k -> new HashSet<>()).add(dstNode);

        log.debug("Added link: {} -> {}",
                String.format("0x%04X", srcNode),
                String.format("0x%04X", dstNode));
    }

    /**
     * Get all active nodes
     */
    public List<WiseNode> getActiveNodes() {
        long now = System.currentTimeMillis();

        return nodes.values().stream()
                .filter(node -> (now - node.lastSeen) < NODE_TIMEOUT_MS)
                .collect(Collectors.toList());
    }

    /**
     * Get node by ID
     */
    public WiseNode getNode(int nodeId) {
        return nodes.get(nodeId);
    }

    /**
     * Get all nodes
     */
    public Collection<WiseNode> getAllNodes() {
        return new ArrayList<>(nodes.values());
    }

    /**
     * Get neighbors of a node
     */
    public Set<Integer> getNeighbors(int nodeId) {
        return links.getOrDefault(nodeId, Collections.emptySet());
    }

    /**
     * Get network topology as map
     */
    public Map<String, Object> getTopology() {
        Map<String, Object> topology = new HashMap<>();

        // Nodes
        List<Map<String, Object>> nodeList = new ArrayList<>();
        for (WiseNode node : getAllNodes()) {
            Map<String, Object> nodeMap = new HashMap<>();
            nodeMap.put("id", node.nodeId);
            nodeMap.put("type", node.nodeType == 0 ? "border-router" : "sensor");
            nodeMap.put("active", node.active);
            nodeMap.put("battery", node.batteryLevel);
            nodeMap.put("lastSeen", node.lastSeen);
            nodeList.add(nodeMap);
        }
        topology.put("nodes", nodeList);

        // Links
        List<Map<String, Object>> linkList = new ArrayList<>();
        for (Map.Entry<Integer, Set<Integer>> entry : links.entrySet()) {
            for (Integer neighbor : entry.getValue()) {
                Map<String, Object> link = new HashMap<>();
                link.put("source", entry.getKey());
                link.put("target", neighbor);
                linkList.add(link);
            }
        }
        topology.put("links", linkList);

        return topology;
    }

    /**
     * Clear stale nodes
     */
    public void cleanupStaleNodes() {
        long now = System.currentTimeMillis();

        nodes.values().stream()
                .filter(node -> (now - node.lastSeen) >= NODE_TIMEOUT_MS)
                .forEach(node -> {
                    node.active = false;
                    log.info("Node {} marked as inactive", String.format("0x%04X", node.nodeId));
                });
    }

    /**
     * Get node count
     */
    public int getNodeCount() {
        return nodes.size();
    }

    /**
     * Get active node count
     */
    public int getActiveNodeCount() {
        return (int) getActiveNodes().stream().count();
    }

    /**
     * Wireless sensor node representation
     */
    public static class WiseNode {
        public int nodeId;
        public byte nodeType; // 0 = border router, 1 = sensor
        public boolean active;
        public int batteryLevel; // 0-100%
        public long lastSeen;

        public WiseNode(int nodeId) {
            this.nodeId = nodeId;
            this.active = true;
            this.batteryLevel = 100;
            this.lastSeen = System.currentTimeMillis();
        }

        @Override
        public String toString() {
            return String.format("WiseNode{id=0x%04X, type=%d, active=%b, battery=%d%%}",
                    nodeId, nodeType, active, batteryLevel);
        }
    }
}
