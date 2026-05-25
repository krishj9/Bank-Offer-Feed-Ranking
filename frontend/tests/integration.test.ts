import { expect, test, describe } from 'vitest';
import { BankOfferApiClient } from '../src/api/client';

describe('End-to-End Integration Pipeline (T-039)', () => {
  test('Flow: sample user -> rank offers -> submit feedback', async () => {
    // 1. Initialize API Client
    const client = new BankOfferApiClient();

    // 2. Probe if live backend is running
    const isBackendOnline = await client.probeBackend();
    
    if (isBackendOnline) {
      console.log('--- [INTEGRATION TEST] Running against LIVE FastAPI backend ---');
      client.setMode(true);
    } else {
      console.log('--- [INTEGRATION TEST] FastAPI backend is OFFLINE. Running in MOCK Fallback mode ---');
      client.setMode(false);
    }

    // 3. Step A: Get Sample Users
    const users = await client.getSampleUsers();
    expect(users).toBeDefined();
    expect(Array.isArray(users)).toBe(true);
    expect(users.length).toBeGreaterThan(0);

    const testUser = users[0];
    expect(testUser.user_id).toBeDefined();
    expect(testUser.age).toBeDefined();
    expect(testUser.job).toBeDefined();

    console.log(`[Integration Test] Step A Passed: Retrieved ${users.length} users. Selected ${testUser.user_id}.`);

    // 4. Step B: Rank Offers for selected user
    const rankResponse = await client.rankOffers(testUser.user_id, true);
    expect(rankResponse).toBeDefined();
    expect(rankResponse.request_id).toBeDefined();
    expect(rankResponse.model_version).toBeDefined();
    expect(rankResponse.generated_at).toBeDefined();
    expect(Array.isArray(rankResponse.results)).toBe(true);

    console.log(`[Integration Test] Step B Passed: Ranked ${rankResponse.results.length} offers using model: ${rankResponse.model_version}`);

    if (rankResponse.results.length > 0) {
      // Verify ranks are sequentially ordered (1, 2, ...) and score descending
      let previousScore = Infinity;
      rankResponse.results.forEach((offer, idx) => {
        expect(offer.rank).toBe(idx + 1);
        expect(offer.offer_id).toBeDefined();
        expect(offer.title).toBeDefined();
        expect(offer.model_score).toBeDefined();
        expect(offer.model_score).toBeLessThanOrEqual(previousScore + 0.0001); // Allowing for floating-point precision
        previousScore = offer.model_score;
      });

      // 5. Step C: Submit Feedback for the top ranked offer
      const topOffer = rankResponse.results[0];
      const feedbackRequest = {
        request_id: rankResponse.request_id,
        user_id: testUser.user_id,
        offer_id: topOffer.offer_id,
        action_type: 'accepted' as const,
        rank_position: topOffer.rank,
        score: topOffer.model_score,
        model_version: topOffer.model_version,
        timestamp: new Date().toISOString(),
      };

      const feedbackResponse = await client.submitFeedback(feedbackRequest);
      expect(feedbackResponse).toBeDefined();
      expect(feedbackResponse.success).toBe(true);
      expect(feedbackResponse.event_id).toBeDefined();
      expect(feedbackResponse.message).toBeDefined();

      console.log(`[Integration Test] Step C Passed: Submitted feedback 'accepted' for offer ${topOffer.offer_id}. Event ID: ${feedbackResponse.event_id}`);
    } else {
      console.log('[Integration Test] Step C Skipped: No eligible offers to submit feedback for.');
    }

    console.log('[Integration Test] Pipeline complete and successful.');
  });
});
