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
- **Acknowledge the limitation professionally** with specific reference to what was asked
- **Offer to draft an email** to the appropriate contact for assistance
- **Suggest Richard Pallangyo** as the default contact when no specific contacts are found
- **Provide related information** that IS available from the knowledge base
- **Use professional, helpful language** that feels conversational and human-like
- **Not make up** specific details, numbers, or processes

## Enhanced Email-Offer Functionality

The RAG agent now includes sophisticated email assistance when information is missing:

### Test Case: Specialized/Technical Queries
**Question**: "What are the specific customs duties for importing a high-energy particle accelerator from Switzerland?"

**Expected Response Pattern**:
```
🔍 **Procurement Information Search**

I searched our UW procurement knowledge base for information about customs duties for importing high-energy particle accelerators from Switzerland, but I couldn't find specific details about this specialized equipment.

📧 **How I Can Help**
For complex international procurement questions like this, I recommend contacting:

**Richard Pallangyo**  
UW Procurement Office  
Email: rapaugustino@gmail.com

Would you like me to help draft an email to Richard requesting information about:
- Customs duties for scientific equipment from Switzerland
- Import procedures for high-energy particle accelerators
- Any special documentation requirements

✅ **What I Can Tell You**
From our procurement policies, I know that international purchases require special consideration for compliance and documentation. [Citation needed if available]
```

### Response Quality Standards
- **Specific**: References the exact item asked about (particle accelerator)
- **Visual**: Uses emojis and formatting for better readability
- **Actionable**: Offers concrete next steps (email drafting)
- **Professional**: Maintains UW procurement context
- **Helpful**: Provides related information when available

### Test Commands for Enhanced Functionality

```bash
# Test specialized equipment query
curl -X POST "http://localhost:8000/agents/query/stream" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the specific customs duties for importing a high-energy particle accelerator from Switzerland?", "conversation_id": "test_email_offer_1"}'

# Test another specialized query
curl -X POST "http://localhost:8000/agents/query/stream" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the procurement requirements for importing medical isotopes from Canada?", "conversation_id": "test_email_offer_2"}'

# Test policy question that should have an answer
curl -X POST "http://localhost:8000/agents/query/stream" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the four key principles of UW procurement policy?", "conversation_id": "test_known_info"}'
```