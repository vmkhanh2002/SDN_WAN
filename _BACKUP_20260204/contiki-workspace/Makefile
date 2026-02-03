# Makefile for SDN-WISE Contiki-NG Applications

CONTIKI_PROJECT = sensor-node
all: $(CONTIKI_PROJECT)

# Contiki-NG directory
CONTIKI = /opt/contiki-ng

# Platform target
TARGET ?= cooja

# Additional source files
PROJECT_SOURCEFILES += sdn-wise-agent.c

# Network stack
MAKE_MAC = MAKE_MAC_CSMA
MAKE_NET = MAKE_NET_IPV6
MAKE_ROUTING = MAKE_ROUTING_RPL_CLASSIC

# UDP support
MODULES += os/net/app-layer/coap

# Logging levels
LOG_CONF_LEVEL_IPV6 = LOG_LEVEL_INFO
LOG_CONF_LEVEL_RPL = LOG_LEVEL_INFO
LOG_CONF_LEVEL_MAC = LOG_LEVEL_WARN

# IMPORTANT: Remove strict .csc requirement for manual builds
# Allow building without Cooja GUI
CONTIKI_WITH_IPV6 = 1

# Include Contiki-NG Makefile
include $(CONTIKI)/Makefile.include
