package org.onosproject.wisesdn;

import org.onlab.packet.Ethernet;
import org.onlab.packet.IPv4;
import org.onlab.packet.UDP;
import org.onosproject.core.ApplicationId;
import org.onosproject.core.CoreService;
import org.onosproject.net.packet.PacketContext;
import org.onosproject.net.packet.PacketPriority;
import org.onosproject.net.packet.PacketProcessor;
import org.onosproject.net.packet.PacketService;
import org.osgi.service.component.annotations.Activate;
import org.osgi.service.component.annotations.Component;
import org.osgi.service.component.annotations.Deactivate;
import org.osgi.service.component.annotations.Reference;
import org.osgi.service.component.annotations.ReferenceCardinality;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * SDN-WISE Application Component
 * Main entry point for wireless sensor network management
 */
@Component(immediate = true)
public class AppComponent {

    private final Logger log = LoggerFactory.getLogger(getClass());

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    protected CoreService coreService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    protected PacketService packetService;

    private ApplicationId appId;
    private WisePacketProcessor processor;
    private WiseController controller;
    private FlowTableManager flowManager;
    private TopologyManager topologyManager;

    // SDN-WISE uses UDP port 9999
    private static final int SDNWISE_PORT = 9999;

    @Activate
    protected void activate() {
        appId = coreService.registerApplication("org.onosproject.wisesdn");

        // Initialize managers
        flowManager = new FlowTableManager();
        topologyManager = new TopologyManager();
        controller = new WiseController(flowManager, topologyManager);

        // Register packet processor
        processor = new WisePacketProcessor();
        packetService.addProcessor(processor, PacketProcessor.director(2));

        // Request UDP packets on SDN-WISE port
        requestIntercepts();

        log.info("SDN-WISE Application Started - App ID: {}", appId.id());
        log.info("Listening for SDN-WISE packets on UDP port {}", SDNWISE_PORT);
    }

    @Deactivate
    protected void deactivate() {
        withdrawIntercepts();
        packetService.removeProcessor(processor);
        processor = null;

        log.info("SDN-WISE Application Stopped");
    }

    /**
     * Request packet intercepts for SDN-WISE traffic
     */
    private void requestIntercepts() {
        // No specific traffic selector needed - we'll filter in processor
        packetService.requestPackets(
                null,
                PacketPriority.REACTIVE,
                appId);
    }

    /**
     * Withdraw packet intercepts
     */
    private void withdrawIntercepts() {
        packetService.cancelPackets(
                null,
                PacketPriority.REACTIVE,
                appId);
    }

    /**
     * Packet processor for SDN-WISE packets
     */
    private class WisePacketProcessor implements PacketProcessor {

        @Override
        public void process(PacketContext context) {
            // Stop processing if the packet has been handled
            if (context.isHandled()) {
                return;
            }

            Ethernet ethPkt = context.inPacket().parsed();

            if (ethPkt == null) {
                return;
            }

            // Check if IPv4
            if (ethPkt.getEtherType() != Ethernet.TYPE_IPV4) {
                return;
            }

            IPv4 ipv4Pkt = (IPv4) ethPkt.getPayload();

            // Check if UDP
            if (ipv4Pkt.getProtocol() != IPv4.PROTOCOL_UDP) {
                return;
            }

            UDP udpPkt = (UDP) ipv4Pkt.getPayload();

            // Check if SDN-WISE port
            if (udpPkt.getDestinationPort() != SDNWISE_PORT) {
                return;
            }

            // Extract SDN-WISE payload
            byte[] payload = udpPkt.getPayload().serialize();

            log.debug("Received SDN-WISE packet: {} bytes from {}",
                    payload.length,
                    context.inPacket().receivedFrom());

            try {
                // Parse and process SDN-WISE packet
                WisePacket wisePacket = WisePacket.parse(payload);
                controller.handlePacket(wisePacket, context);

            } catch (Exception e) {
                log.error("Error processing SDN-WISE packet", e);
            }
        }
    }

    /**
     * Get the flow table manager instance
     */
    public FlowTableManager getFlowManager() {
        return flowManager;
    }

    /**
     * Get the topology manager instance
     */
    public TopologyManager getTopologyManager() {
        return topologyManager;
    }

    /**
     * Get the controller instance
     */
    public WiseController getController() {
        return controller;
    }

    /**
     * Get the application ID
     */
    public ApplicationId getAppId() {
        return appId;
    }
}
