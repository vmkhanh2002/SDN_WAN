package org.onosproject.wisesdn;

/**
 * Flow Rule for SDN-WISE sensor nodes
 * Represents a forwarding rule in a sensor's flow table
 */
public class FlowRule {

    private int nodeId; // Node where this flow is installed
    private int srcAddr; // Source address match
    private int dstAddr; // Destination address match
    private byte action; // Action to take (FORWARD, DROP, etc.)
    private int nextHop; // Next hop address
    private long timestamp; // Installation timestamp

    // Actions
    public static final byte ACTION_DROP = 0;
    public static final byte ACTION_FORWARD = 1;
    public static final byte ACTION_MODIFY = 2;
    public static final byte ACTION_AGGREGATE = 3;

    public FlowRule() {
        this.timestamp = System.currentTimeMillis();
    }

    public FlowRule(int nodeId, int srcAddr, int dstAddr, byte action, int nextHop) {
        this.nodeId = nodeId;
        this.srcAddr = srcAddr;
        this.dstAddr = dstAddr;
        this.action = action;
        this.nextHop = nextHop;
        this.timestamp = System.currentTimeMillis();
    }

    // Getters and setters
    public int getNodeId() {
        return nodeId;
    }

    public void setNodeId(int nodeId) {
        this.nodeId = nodeId;
    }

    public int getSrcAddr() {
        return srcAddr;
    }

    public void setSrcAddr(int srcAddr) {
        this.srcAddr = srcAddr;
    }

    public int getDstAddr() {
        return dstAddr;
    }

    public void setDstAddr(int dstAddr) {
        this.dstAddr = dstAddr;
    }

    public byte getAction() {
        return action;
    }

    public void setAction(byte action) {
        this.action = action;
    }

    public int getNextHop() {
        return nextHop;
    }

    public void setNextHop(int nextHop) {
        this.nextHop = nextHop;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(long timestamp) {
        this.timestamp = timestamp;
    }

    @Override
    public String toString() {
        return String.format("FlowRule{nodeId=0x%04X, src=0x%04X, dst=0x%04X, action=%d, nextHop=0x%04X}",
                nodeId, srcAddr, dstAddr, action, nextHop);
    }

    @Override
    public boolean equals(Object o) {
        if (this == o)
            return true;
        if (o == null || getClass() != o.getClass())
            return false;

        FlowRule flowRule = (FlowRule) o;

        if (nodeId != flowRule.nodeId)
            return false;
        if (srcAddr != flowRule.srcAddr)
            return false;
        if (dstAddr != flowRule.dstAddr)
            return false;
        if (action != flowRule.action)
            return false;
        return nextHop == flowRule.nextHop;
    }

    @Override
    public int hashCode() {
        int result = nodeId;
        result = 31 * result + srcAddr;
        result = 31 * result + dstAddr;
        result = 31 * result + (int) action;
        result = 31 * result + nextHop;
        return result;
    }
}
