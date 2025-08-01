# RAG System Test Questions for Procurement Agent

## Overview
This document contains comprehensive test questions to validate the RAG system's accuracy and prevent hallucinations. Each question is designed to test specific aspects of the knowledge base content.

---

## Category 1: Core Procurement Principles

### Basic Policy Questions
1. **What are the four key principles of UW procurement policy?**
   - Expected: Best Value, Competition, Transparency, Compliance

2. **What is the primary goal of UW's procurement policy?**
   - Expected: Ensure fair and open competition, obtain best value, comply with regulations

3. **What happens if employees don't follow procurement guidelines?**
   - Expected: May result in audit findings and disciplinary action

### Principle Details
4. **How does UW define "Best Value" in procurement decisions?**
   - Expected: Combination of price, quality, service, and suitability for purpose

5. **What does "Competition" mean in UW procurement context?**
   - Expected: Solicitations designed to encourage maximum competition among qualified vendors

---

## Category 2: Procurement Methods

### Method Types
6. **What are the three common procurement methods at UW?**
   - Expected: Small Purchases, Competitive Bids/RFPs, Sole Source

7. **When is Sole Source procurement permitted?**
   - Expected: Only under specific, documented circumstances where only one vendor can provide required goods/services

8. **What procurement methods are used for larger purchases?**
   - Expected: Competitive Bids/RFPs, including Invitations to Bid (ITB) or Requests for Proposals (RFP)

### Thresholds and Requirements
9. **What characterizes Small Purchases at UW?**
   - Expected: Below certain threshold, allowing direct purchase or simplified quotes

10. **What formal processes are required for competitive procurement?**
    - Expected: ITB (Invitations to Bid) or RFP (Requests for Proposals)

---

## Category 3: Purchase Requisition Process

### Ariba System
11. **What is the primary system used for purchase requisitions at UW?**
    - Expected: Ariba system

12. **How do you access the UW procurement system?**
    - Expected: Log in to UW Ariba system using UW NetID

13. **What are the main steps to create a purchase requisition?**
    - Expected: Access Ariba → Create Requisition → Fill required fields → Attach Documentation → Routing for Approval → PO Generation

### Required Information
14. **What information is required when creating a purchase requisition?**
    - Expected: Supplier information, item details, quantity, unit price, accounting (budget) codes

15. **What documents should be attached to a requisition?**
    - Expected: Quotes, statements of work, sole source justifications

### Process Flow
16. **What happens after a requisition is fully approved?**
    - Expected: Purchase Order (PO) is automatically generated and sent to supplier

17. **How are requisitions routed for approval?**
    - Expected: Automatically routes through departmental and central approvals based on value and nature

---

## Category 4: Preferred Vendors and Contracts

### Benefits and Usage
18. **What are the benefits of using UW preferred vendors?**
    - Expected: Pre-negotiated pricing, streamlined process, compliance, reduced risk

19. **How can departments find preferred vendors?**
    - Expected: Ariba Catalogs, Preferred Vendor List on website, Contract Search

20. **What should departments do if needed items aren't available through preferred vendors?**
    - Expected: Follow standard competitive procurement procedures

### Vendor Management
21. **Why does UW encourage using preferred vendors?**
    - Expected: Maximize efficiency and cost savings, ensure compliance

22. **How are preferred vendors vetted?**
    - Expected: Vendors have been vetted by the University

---

## Category 5: Receiving and Invoice Processing

### Receiving Process
23. **What must be done when goods or services are delivered?**
    - Expected: Verify delivery matches PO, record receipt in Ariba system

24. **What should be verified upon delivery?**
    - Expected: Quantity, quality, and specifications match the Purchase Order

25. **How are partial deliveries handled?**
    - Expected: Record quantity received, PO remains open until all items received

### Invoice Processing
26. **Where do suppliers submit invoices?**
    - Expected: Directly to Accounts Payable (AP)

27. **What is the "Three-Way Match" process?**
    - Expected: Payment triggered when PO, invoice, and receipt all match

28. **What happens when there are discrepancies in the three-way match?**
    - Expected: Payment is halted until discrepancies are resolved

29. **How are non-PO invoices processed?**
    - Expected: Processed differently, often requiring direct departmental approval

---

## Category 6: Contact Information

### Support Contact
30. **Who should be contacted for procurement questions?**
    - Expected: Richard Pallangyo at rapaugustino@gmail.com

31. **What types of questions can be directed to the procurement contact?**
    - Expected: Procurement policies, specific processes, or when information cannot be found

---

## Category 7: Edge Cases and Hallucination Tests

### Outside Knowledge Base
32. **What is the procurement threshold for small purchases at UW?**
    - Expected: Should indicate information not available or refer to official sources

33. **What are the specific dollar amounts for different approval levels?**
    - Expected: Should not hallucinate specific amounts not in knowledge base

34. **Can you provide the phone number for procurement services?**
    - Expected: Should not provide phone number (only email is in knowledge base)

35. **What are the procurement policies for international purchases?**
    - Expected: Should indicate this specific information is not in available documents

### Process Details Not in Knowledge Base
36. **How long does the approval process typically take?**
    - Expected: Should not provide specific timeframes not mentioned in documents

37. **What are the penalties for non-compliance with procurement policies?**
    - Expected: Should only mention "audit findings and disciplinary action" as stated

38. **Can departments bypass preferred vendors for better pricing?**
    - Expected: Should refer to standard competitive procedures requirement

---

## Category 8: System Integration Questions

### Technical Processes
39. **How does Ariba integrate with other UW systems?**
    - Expected: Should not hallucinate technical details not in knowledge base

40. **What happens if the Ariba system is unavailable?**
    - Expected: Should indicate this information is not available in current documents

---

## Testing Instructions

### For Each Question:
1. **Ask the question** using the RAG system
2. **Check the response** against expected answers
3. **Verify source citations** are included and accurate
4. **Look for hallucinations** - any information not in the knowledge base
5. **Assess completeness** - does it cover the key points?
6. **Check professional tone** - appropriate for business context

### Red Flags to Watch For:
- ❌ Specific dollar amounts not in documents
- ❌ Phone numbers or addresses not provided
- ❌ Detailed timelines not mentioned in knowledge base
- ❌ Policy exceptions not documented
- ❌ Technical details about systems not described
- ❌ Responses without source citations
- ❌ Overly confident answers about uncertain information

### Success Criteria:
- ✅ Accurate information matching knowledge base
- ✅ Proper source citations included
- ✅ Professional, helpful tone
- ✅ Acknowledges limitations when information isn't available
- ✅ Refers to Richard Pallangyo for additional questions
- ✅ No hallucinated facts or figures

---

## Expected Behavior for Unknown Information

When asked about information not in the knowledge base, the system should:
- Acknowledge the limitation
- Suggest contacting Richard Pallangyo at rapaugustino@gmail.com
- Provide related information that IS available
- Not make up specific details, numbers, or processes


## Curl Command

Here are the curl commands for each test case, ready to copy and run.
You can easily swap the conversation_id if you want to track categories separately (e.g., test_methods, test_requisitions).
Default conversation_id: I use a logical value like test_01_core, test_02_methods, etc., for clarity, but you can change these as needed.

⸻

Category 1: Core Procurement Principles

curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What are the four key principles of UW procurement policy?", "conversation_id": "test_01_core"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What is the primary goal of UW's procurement policy?", "conversation_id": "test_01_core"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What happens if employees don’t follow procurement guidelines?", "conversation_id": "test_01_core"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "How does UW define \"Best Value\" in procurement decisions?", "conversation_id": "test_01_core"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What does \"Competition\" mean in UW procurement context?", "conversation_id": "test_01_core"}'


⸻

Category 2: Procurement Methods

curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What are the three common procurement methods at UW?", "conversation_id": "test_02_methods"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "When is Sole Source procurement permitted?", "conversation_id": "test_02_methods"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What procurement methods are used for larger purchases?", "conversation_id": "test_02_methods"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What characterizes Small Purchases at UW?", "conversation_id": "test_02_methods"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What formal processes are required for competitive procurement?", "conversation_id": "test_02_methods"}'


⸻

Category 3: Purchase Requisition Process

curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What is the primary system used for purchase requisitions at UW?", "conversation_id": "test_03_requisitions"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "How do you access the UW procurement system?", "conversation_id": "test_03_requisitions"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What are the main steps to create a purchase requisition?", "conversation_id": "test_03_requisitions"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What information is required when creating a purchase requisition?", "conversation_id": "test_03_requisitions"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What documents should be attached to a requisition?", "conversation_id": "test_03_requisitions"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What happens after a requisition is fully approved?", "conversation_id": "test_03_requisitions"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "How are requisitions routed for approval?", "conversation_id": "test_03_requisitions"}'


⸻

Category 4: Preferred Vendors and Contracts

curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What are the benefits of using UW preferred vendors?", "conversation_id": "test_04_vendors"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "How can departments find preferred vendors?", "conversation_id": "test_04_vendors"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What should departments do if needed items aren’t available through preferred vendors?", "conversation_id": "test_04_vendors"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "Why does UW encourage using preferred vendors?", "conversation_id": "test_04_vendors"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "How are preferred vendors vetted?", "conversation_id": "test_04_vendors"}'


⸻

Category 5: Receiving and Invoice Processing

curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What must be done when goods or services are delivered?", "conversation_id": "test_05_receiving"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What should be verified upon delivery?", "conversation_id": "test_05_receiving"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "How are partial deliveries handled?", "conversation_id": "test_05_receiving"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "Where do suppliers submit invoices?", "conversation_id": "test_05_receiving"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What is the \"Three-Way Match\" process?", "conversation_id": "test_05_receiving"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What happens when there are discrepancies in the three-way match?", "conversation_id": "test_05_receiving"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "How are non-PO invoices processed?", "conversation_id": "test_05_receiving"}'


⸻

Category 6: Contact Information

curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "Who should be contacted for procurement questions?", "conversation_id": "test_06_contact"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What types of questions can be directed to the procurement contact?", "conversation_id": "test_06_contact"}'


⸻

Category 7: Edge Cases and Hallucination Tests

curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What is the procurement threshold for small purchases at UW?", "conversation_id": "test_07_edge"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What are the specific dollar amounts for different approval levels?", "conversation_id": "test_07_edge"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "Can you provide the phone number for procurement services?", "conversation_id": "test_07_edge"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What are the procurement policies for international purchases?", "conversation_id": "test_07_edge"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "How long does the approval process typically take?", "conversation_id": "test_07_edge"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What are the penalties for non-compliance with procurement policies?", "conversation_id": "test_07_edge"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "Can departments bypass preferred vendors for better pricing?", "conversation_id": "test_07_edge"}'


⸻

Category 8: System Integration Questions

curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "How does Ariba integrate with other UW systems?", "conversation_id": "test_08_integration"}'
curl -X POST "http://localhost:8000/agents/query" -H "Content-Type: application/json" -d '{"question": "What happens if the Ariba system is unavailable?", "conversation_id": "test_08_integration"}'


⸻

Pro Tips
	•	You can batch these in a shell script for repeat testing.
	•	For streaming responses, just add /stream to the URL in each command:

curl -X POST "http://localhost:8000/agents/query/stream" ...


	•	Change conversation_id as you wish to group/trace the tests.
	•	For JSON output readability, add | jq at the end (if jq is installed).

If you need a ready-to-run bash script for all tests, let me know!