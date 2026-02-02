package org.onosproject.wisesdn;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * Flow Table Manager
 * Manages flow rules for sensor nodes in the WSN
 */
public class FlowTableManager {

    private static final Logger log = LoggerFactory.getLogger(FlowTableManager.class);

    // Flow tables: nodeId -> list of flow rules
    private final Map<Integer, List<FlowRule>> flowTables = new ConcurrentHashMap<>();

    // Flow installation status
    private final Map<String, FlowInstallStatus> installStatus = new ConcurrentHashMap<>();

    /**
     * Install a flow rule to a node
     */
    public String installFlow(FlowRule rule) {
        log.info("Installing flow: {} on node {}", rule, String.format("0x%04X", rule.getNodeId()));

        // Add to flow table
        flowTables.computeIfAbsent(rule.getNodeId(), k -> new ArrayList<>()).add(rule);

        // Track installation status
        String flowId = generateFlowId(rule);
        installStatus.put(flowId, FlowInstallStatus.PENDING);

        log.debug("Flow {} added to table, status: PENDING", flowId);

        return flowId;
    }

    /**
     * Get all flows for a node
     */
    public List<FlowRule> getFlows(int nodeId) {
        return flowTables.getOrDefault(nodeId, Collections.emptyList());
    }

    /**
     * Get matching flow rule for a packet
     */
    public FlowRule getMatchingFlow(int srcNode, int dstNode) {
        List<FlowRule> rules = flowTables.get(srcNode);

        if (rules == null) {
            return null;
        }

        // Find first matching rule
        return rules.stream()
                .filter(rule -> rule.getSrcAddr() == srcNode && rule.getDstAddr() == dstNode)
                .findFirst()
                .orElse(null);
    }

    /**
     * Delete a flow rule
     */
    public boolean deleteFlow(int nodeId, String flowId) {
        List<FlowRule> rules = flowTables.get(nodeId);

        if (rules == null) {
            return false;
        }

        boolean removed = rules.removeIf(rule -> generateFlowId(rule).equals(flowId));

        if (removed) {
            log.info("Flow {} deleted from node {}", flowId, String.format("0x%04X", nodeId));
            installStatus.remove(flowId);
        }

        return removed;
    }

    /**
     * Delete all flows for a node
     */
    public void deleteAllFlows(int nodeId) {
        List<FlowRule> rules = flowTables.remove(nodeId);

        if (rules != null) {
            log.info("Deleted {} flows from node {}", rules.size(), String.format("0x%04X", nodeId));

            // Clean up install status
            rules.forEach(rule -> installStatus.remove(generateFlowId(rule)));
        }
    }

    /**
     * Mark flow as installed
     */
    public void markFlowInstalled(int nodeId) {
        // Find pending flows for this node and mark as installed
        flowTables.getOrDefault(nodeId, Collections.emptyList())
                .forEach(rule -> {
                    String flowId = generateFlowId(rule);
                    installStatus.put(flowId, FlowInstallStatus.INSTALLED);
                    log.debug("Flow {} marked as INSTALLED", flowId);
                });
    }

    /**
     * Get flow installation status
     */
    public FlowInstallStatus getFlowStatus(String flowId) {
        return installStatus.getOrDefault(flowId, FlowInstallStatus.UNKNOWN);
    }

    /**
     * Get all flow tables
     */
    public Map<Integer, List<FlowRule>> getAllFlowTables() {
        return new HashMap<>(flowTables);
    }

    /**
     * Get total flow count across all nodes
     */
    public int getTotalFlowCount() {
        return flowTables.values().stream()
                .mapToInt(List::size)
                .sum();
    }

    /**
     * Get nodes with flows
     */
    public Set<Integer> getNodesWithFlows() {
        return new HashSet<>(flowTables.keySet());
    }

    /**
     * Generate unique flow ID
     */
    private String generateFlowId(FlowRule rule) {
        return String.format("flow-%04X-%04X-%04X-%d",
                rule.getNodeId(), rule.getSrcAddr(), rule.getDstAddr(), rule.getAction());
    }

    /**
     * Flow installation status enum
     */
    public enum FlowInstallStatus {
        PENDING,
        INSTALLED,
        FAILED,
        UNKNOWN
    }
}
