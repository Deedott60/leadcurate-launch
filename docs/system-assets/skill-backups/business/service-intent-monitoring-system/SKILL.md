---
name: service-intent-monitoring-system
description: "Find, score, review, and route public social/forum posts where people are actively asking for a local service."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [leadgen, monitoring, local-services, intent, routing]
---

# Service Intent Monitoring System

Use when Derrick wants a product/service that finds people publicly asking for local services and routes those opportunities to a business.

## Product idea
A human-reviewed intent feed that monitors public sources for service requests, classifies them, and routes approved opportunities to clients by city and niche.

## Best sources first
- Reddit local communities
- public local forums / request boards
- optional X if access is viable
- public Facebook pages only as a secondary/manual source

## Avoid as core automation
- private Facebook groups
- closed neighborhood networks
- anything that requires brittle or policy-unsafe access

## Workflow
1. monitor public sources
2. detect request intent
3. infer niche + location
4. score urgency/confidence
5. queue for review
6. approve/reject
7. route to client via dashboard/email/CRM/webhook

## Rules
- do not promise fully automated outbound replies everywhere
- prefer detect + review + route first
- sell vetted opportunities, not guaranteed booked jobs
- start with one urgent niche and a small city set

## Best first niche
Emergency home services, especially plumbers.
