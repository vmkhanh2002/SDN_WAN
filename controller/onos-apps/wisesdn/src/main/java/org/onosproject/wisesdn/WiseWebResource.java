package org.onosproject.wisesdn;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.onosproject.rest.AbstractWebResource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.ws.rs.*;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;
import java.util.List;
import java.util.Map;

/**
 * REST API for SDN-WISE WSN Management
 */
@Path("wisesdn")
public class WiseWebResource extends AbstractWebResource {

    private final Logger log = LoggerFactory.getLogger(getClass());
    private final ObjectMapper mapper = new ObjectMapper();

    /**
     * Get all WSN devices
     * GET /onos/wisesdn/api/devices
     */
    @GET
    @Path("api/devices")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getDevices() {
        try {
            AppComponent app = get(AppComponent.class);
            TopologyManager topologyMgr = app.getTopologyManager();

            ArrayNode devices = mapper.createArrayNode();

            for (TopologyManager.WiseNode node : topologyMgr.getAllNodes()) {
                ObjectNode deviceNode = mapper.createObjectNode();
                deviceNode.put("nodeId", node.nodeId);
                deviceNode.put("type", node.nodeType == 0 ? "border-router" : "sensor");
                deviceNode.put("active", node.active);
                deviceNode.put("battery", node.batteryLevel);
                deviceNode.put("lastSeen", node.lastSeen);

                // Get flow count for this node
                int flowCount = app.getFlowManager().getFlows(node.nodeId).size();
                deviceNode.put("flowCount", flowCount);

                devices.add(deviceNode);
            }

            return Response.ok(devices.toString()).build();

        } catch (Exception e) {
            log.error("Error getting devices", e);
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity("{\"error\":\"" + e.getMessage() + "\"}").build();
        }
    }

    /**
     * Get flows for a specific node
     * GET /onos/wisesdn/api/flows/{nodeId}
     */
    @GET
    @Path("api/flows/{nodeId}")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getFlows(@PathParam("nodeId") int nodeId) {
        try {
            AppComponent app = get(AppComponent.class);
            FlowTableManager flowMgr = app.getFlowManager();

            List<FlowRule> flows = flowMgr.getFlows(nodeId);

            ArrayNode flowArray = mapper.createArrayNode();
            for (FlowRule flow : flows) {
                ObjectNode flowNode = mapper.createObjectNode();
                flowNode.put("nodeId", flow.getNodeId());
                flowNode.put("srcAddr", flow.getSrcAddr());
                flowNode.put("dstAddr", flow.getDstAddr());
                flowNode.put("action", flow.getAction());
                flowNode.put("nextHop", flow.getNextHop());
                flowNode.put("timestamp", flow.getTimestamp());
                flowArray.add(flowNode);
            }

            ObjectNode result = mapper.createObjectNode();
            result.put("nodeId", nodeId);
            result.set("flows", flowArray);

            return Response.ok(result.toString()).build();

        } catch (Exception e) {
            log.error("Error getting flows for node {}", nodeId, e);
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity("{\"error\":\"" + e.getMessage() + "\"}").build();
        }
    }

    /**
     * Install a flow rule
     * POST /onos/wisesdn/api/flows
     */
    @POST
    @Path("api/flows")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response installFlow(String flowJson) {
        try {
            // Parse flow rule from JSON
            ObjectNode flowNode = (ObjectNode) mapper.readTree(flowJson);

            int nodeId = flowNode.get("nodeId").asInt();
            int srcAddr = flowNode.get("srcAddr").asInt();
            int dstAddr = flowNode.get("dstAddr").asInt();
            byte action = (byte) flowNode.get("action").asInt();
            int nextHop = flowNode.get("nextHop").asInt();

            FlowRule rule = new FlowRule(nodeId, srcAddr, dstAddr, action, nextHop);

            AppComponent app = get(AppComponent.class);
            String flowId = app.getFlowManager().installFlow(rule);

            ObjectNode response = mapper.createObjectNode();
            response.put("status", "success");
            response.put("flowId", flowId);
            response.put("message", "Flow rule installed");

            log.info("Flow installed: {} on node {}", flowId, String.format("0x%04X", nodeId));

            return Response.ok(response.toString()).build();

        } catch (Exception e) {
            log.error("Error installing flow", e);
            ObjectNode error = mapper.createObjectNode();
            error.put("status", "error");
            error.put("message", e.getMessage());
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(error.toString()).build();
        }
    }

    /**
     * Get WSN topology
     * GET /onos/wisesdn/api/topology
     */
    @GET
    @Path("api/topology")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getTopology() {
        try {
            AppComponent app = get(AppComponent.class);
            TopologyManager topologyMgr = app.getTopologyManager();

            Map<String, Object> topology = topologyMgr.getTopology();

            return Response.ok(mapper.writeValueAsString(topology)).build();

        } catch (Exception e) {
            log.error("Error getting topology", e);
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity("{\"error\":\"" + e.getMessage() + "\"}").build();
        }
    }

    /**
     * Get node statistics
     * GET /onos/wisesdn/api/stats/{nodeId}
     */
    @GET
    @Path("api/stats/{nodeId}")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getStats(@PathParam("nodeId") int nodeId) {
        try {
            AppComponent app = get(AppComponent.class);
            WiseController controller = app.getController();

            WiseController.NodeStats stats = controller.getNodeStats(nodeId);

            if (stats == null) {
                return Response.status(Response.Status.NOT_FOUND)
                        .entity("{\"error\":\"Node not found\"}").build();
            }

            ObjectNode statsNode = mapper.createObjectNode();
            statsNode.put("nodeId", nodeId);
            statsNode.put("battery", stats.batteryLevel);
            statsNode.put("packetsSent", stats.packetsSent);
            statsNode.put("packetsReceived", stats.packetsReceived);
            statsNode.put("lastSeen", stats.lastSeen);

            return Response.ok(statsNode.toString()).build();

        } catch (Exception e) {
            log.error("Error getting stats for node {}", nodeId, e);
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity("{\"error\":\"" + e.getMessage() + "\"}").build();
        }
    }

    /**
     * Set patient consent (Compliance)
     * POST /onos/wisesdn/api/policy/consent
     */
    @POST
    @Path("api/policy/consent")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response setConsent(String json) {
        try {
            ObjectNode root = (ObjectNode) mapper.readTree(json);
            int nodeId = root.get("nodeId").asInt();
            boolean consent = root.get("consent").asBoolean();

            AppComponent app = get(AppComponent.class);
            app.getController().setPatientConsent(nodeId, consent);

            ObjectNode result = mapper.createObjectNode();
            result.put("status", "success");
            result.put("message", "Consent updated");
            result.put("nodeId", nodeId);
            result.put("consent", consent);

            return Response.ok(result.toString()).build();
        } catch (Exception e) {
            log.error("Error setting consent", e);
            return Response.status(Response.Status.BAD_REQUEST).entity("{\"error\":\"" + e.getMessage() + "\"}")
                    .build();
        }
    }

    /**
     * Get patient consent status
     * GET /onos/wisesdn/api/policy/consent/{nodeId}
     */
    @GET
    @Path("api/policy/consent/{nodeId}")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getConsent(@PathParam("nodeId") int nodeId) {
        try {
            AppComponent app = get(AppComponent.class);
            boolean consent = app.getController().getPatientConsent(nodeId);

            ObjectNode result = mapper.createObjectNode();
            result.put("nodeId", nodeId);
            result.put("consent", consent);

            return Response.ok(result.toString()).build();
        } catch (Exception e) {
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity("{\"error\":\"" + e.getMessage() + "\"}").build();
        }
    }

    /**
     * Register device identity
     * POST /onos/wisesdn/api/policy/register
     */
    @POST
    @Path("api/policy/register")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response registerDevice(String json) {
        try {
            ObjectNode root = (ObjectNode) mapper.readTree(json);
            int nodeId = root.get("nodeId").asInt();
            String identity = root.get("identity").asText();

            AppComponent app = get(AppComponent.class);
            app.getController().registerDevice(nodeId, identity);

            ObjectNode result = mapper.createObjectNode();
            result.put("status", "success");
            result.put("message", "Device registered");
            result.put("nodeId", nodeId);
            result.put("identity", identity);

            return Response.ok(result.toString()).build();
        } catch (Exception e) {
            log.error("Error registering device", e);
            return Response.status(Response.Status.BAD_REQUEST).entity("{\"error\":\"" + e.getMessage() + "\"}")
                    .build();
        }
    }
}
