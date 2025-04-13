# Monetization

The service uses a pay-as-you-go model since each alert can be processed at different levels (Base/Pro/Reasoning):

## Alert Modes
- **Base Alert**
  - Data from webscraping only
  
- **Pro Alert**
  - Data from webscraping, webhooks, and APIs
  - Includes an LLM output response
  
- **Reasoning Alert**
  - Data from webscraping, webhooks, and APIs
  - Includes an LLM output response
  - Reasons on the intent of the alert

## Cost Structure

1. **Creation Cost** (one-time per alert)
   Base Alert: X credits
   Pro Alert: 2X credits
   Reasoning Alert: 3X credits


2. **Delivery Cost** (per alert triggered)
   Base Alert: Y credits
   Pro Alert: Y credits
   Reasoning Alert: 2Y credits


## Credit System
- Purchase credits upfront
- Credits don't expire
- Bulk purchase discounts available
- Example credit packages:  # these prices are placeholders
  - Starter: 100 credits ($10)
  - Pro: 1000 credits ($40)
  - Enterprise: 10000 credits ($100)

## Example Usage
"Alert me when Apple stock drops 5%" as a Base alert:
- Creation: X credits
- Each alert delivery: Y credits

"Tell me when it's a good time to visit Paris" as a Reasoning alert:
- Creation: 2X credits
- Each alert delivery: 2Y credits