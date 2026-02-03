package org.onosproject.wisesdn;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.ByteBuffer;

/**
 * SDN-WISE Packet Parser
 * Handles parsing and serialization of SDN-WISE protocol packets
 */
public class WisePacket {

    private static final Logger log = LoggerFactory.getLogger(WisePacket.class);

    // SDN-WISE header fields
    private byte netId; // Network ID
    private byte len; // Packet length
    private int dst; // Destination address (2 bytes)
    private int src; // Source address (2 bytes)
    private byte typ; // Type
    private byte ttl; // Time to live
    private int nxh; // Next hop (2 bytes)

    private byte[] payload; // Payload data

    // Packet types
    public static final byte TYPE_DATA = 0;
    public static final byte TYPE_CONFIG = 1;
    public static final byte TYPE_FLOW_RULE = 2;
    public static final byte TYPE_TOPOLOGY = 3;
    public static final byte TYPE_STATS = 4;

    /**
     * Parse SDN-WISE packet from byte array
     */
    public static WisePacket parse(byte[] data) throws IllegalArgumentException {
        if (data == null || data.length < 11) {
            throw new IllegalArgumentException("Invalid SDN-WISE packet: too short");
        }

        WisePacket packet = new WisePacket();
        ByteBuffer buffer = ByteBuffer.wrap(data);

        packet.netId = buffer.get();
        packet.len = buffer.get();
        packet.dst = buffer.getShort() & 0xFFFF;
        packet.src = buffer.getShort() & 0xFFFF;
        packet.typ = buffer.get();
        packet.ttl = buffer.get();
        packet.nxh = buffer.getShort() & 0xFFFF;

        // Extract payload
        int payloadLen = (packet.len & 0xFF) - 11;
        if (payloadLen > 0 && buffer.remaining() >= payloadLen) {
            packet.payload = new byte[payloadLen];
            buffer.get(packet.payload);
        }

        return packet;
    }

    /**
     * Serialize packet to byte array
     */
    public byte[] serialize() {
        int totalLen = 11 + (payload != null ? payload.length : 0);
        ByteBuffer buffer = ByteBuffer.allocate(totalLen);

        buffer.put(netId);
        buffer.put((byte) totalLen);
        buffer.putShort((short) dst);
        buffer.putShort((short) src);
        buffer.put(typ);
        buffer.put(ttl);
        buffer.putShort((short) nxh);

        if (payload != null) {
            buffer.put(payload);
        }

        return buffer.array();
    }

    // Getters and setters
    public byte getNetId() {
        return netId;
    }

    public void setNetId(byte netId) {
        this.netId = netId;
    }

    public byte getLen() {
        return len;
    }

    public void setLen(byte len) {
        this.len = len;
    }

    public int getDst() {
        return dst;
    }

    public void setDst(int dst) {
        this.dst = dst;
    }

    public int getSrc() {
        return src;
    }

    public void setSrc(int src) {
        this.src = src;
    }

    public byte getTyp() {
        return typ;
    }

    public void setTyp(byte typ) {
        this.typ = typ;
    }

    public byte getTtl() {
        return ttl;
    }

    public void setTtl(byte ttl) {
        this.ttl = ttl;
    }

    public int getNxh() {
        return nxh;
    }

    public void setNxh(int nxh) {
        this.nxh = nxh;
    }

    public byte[] getPayload() {
        return payload;
    }

    public void setPayload(byte[] payload) {
        this.payload = payload;
    }

    @Override
    public String toString() {
        return String.format("WisePacket{netId=%d, len=%d, dst=0x%04X, src=0x%04X, typ=%d, ttl=%d, nxh=0x%04X}",
                netId, len & 0xFF, dst, src, typ, ttl, nxh);
    }
}
