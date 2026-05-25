import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../src/App';
import { apiClient, MOCK_USERS, type RankResponse } from '../src/api/client';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

// Prepare Mock Data
const mockUsers = MOCK_USERS.slice(0, 3); // demo_user_001, demo_user_002, demo_user_003

const mockRankResponse: RankResponse = {
  request_id: 'REQ-TST123',
  model_version: 'xgboost-v1.0-test',
  feature_version: 'v1.0-test',
  generated_at: '2026-05-24T12:00:00.000Z',
  results: [
    {
      rank: 1,
      offer_id: 'OFR-001',
      offer_type: 'term_deposit_reminder',
      title: 'Test High-Yield Term Deposit',
      model_score: 0.92,
      normalized_score: 0.92,
      explanation: 'Highly recommended for testing purposes.',
      model_version: 'xgboost-v1.0-test',
      request_id: 'REQ-TST123',
      rerank_factors: {
        raw_rank: 1,
        reranked_rank: 1,
        priority_boost: 0.0,
      },
    },
    {
      rank: 2,
      offer_id: 'OFR-002',
      offer_type: 'savings_boost',
      title: 'Test Savings Rate Boost',
      model_score: 0.81,
      normalized_score: 0.81,
      explanation: 'Recommended due to test parameters.',
      model_version: 'xgboost-v1.0-test',
      request_id: 'REQ-TST123',
      rerank_factors: {
        raw_rank: 2,
        reranked_rank: 2,
        priority_boost: 0.0,
      },
    },
  ],
};

const mockHealthResponse = {
  status: 'ok',
  model_ready: true,
  artifacts_dir: 'test_artifacts',
  artifact_status: {
    model: true,
    preprocessor: true,
    manifest: true,
  },
};

const mockFeedbackResponse = {
  success: true,
  event_id: 'EVT-TST999',
  message: 'Mock feedback recorded successfully',
};

describe('Frontend Application (App.tsx)', () => {
  let checkHealthSpy: any;
  let rankOffersSpy: any;
  let submitFeedbackSpy: any;
  let setModeSpy: any;

  beforeEach(() => {
    // Spy on the apiClient methods
    vi.spyOn(apiClient, 'probeBackend').mockResolvedValue(false);
    checkHealthSpy = vi.spyOn(apiClient, 'checkHealth').mockResolvedValue(mockHealthResponse);
    vi.spyOn(apiClient, 'getSampleUsers').mockResolvedValue(mockUsers);
    rankOffersSpy = vi.spyOn(apiClient, 'rankOffers').mockResolvedValue(mockRankResponse);
    submitFeedbackSpy = vi.spyOn(apiClient, 'submitFeedback').mockResolvedValue(mockFeedbackResponse);
    setModeSpy = vi.spyOn(apiClient, 'setMode').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders application with correct headers, sidebar, and initial state', async () => {
    render(<App />);

    // Check App Title
    expect(screen.getByText('NovaBank Offer Feed')).toBeDefined();
    expect(screen.getByText(/Real-Time ML Personalization/)).toBeDefined();

    // Check Demographic Selector
    expect(screen.getByText('Demographic Selector')).toBeDefined();

    // Wait for the mock users to load and display in sidebar
    await waitFor(() => {
      expect(screen.getByText(`${mockUsers.length} Profiles`)).toBeDefined();
    });

    // Check mock users rendered in list
    expect(screen.getAllByText(new RegExp(mockUsers[0].user_id)).length).toBeGreaterThan(0);
    expect(screen.getAllByText(new RegExp(mockUsers[1].user_id)).length).toBeGreaterThan(0);
    expect(screen.getAllByText(new RegExp(mockUsers[2].user_id)).length).toBeGreaterThan(0);

    // Initial audit feedback stream state
    expect(screen.getByText('No actions submitted yet')).toBeDefined();
  });

  it('renders ranked offer feed and diagnostic details', async () => {
    render(<App />);

    // Wait for ranking to load
    await waitFor(() => {
      expect(screen.getByText('Test High-Yield Term Deposit')).toBeDefined();
    });

    // Verify offers are rendered
    expect(screen.getByText('Test Savings Rate Boost')).toBeDefined();
    expect(screen.getByText('ID: OFR-001')).toBeDefined();
    expect(screen.getByText('ID: OFR-002')).toBeDefined();

    // Verify explanation/justification
    expect(screen.getByText('Highly recommended for testing purposes.')).toBeDefined();
    expect(screen.getByText('Recommended due to test parameters.')).toBeDefined();

    // Verify Rank graphic
    expect(screen.getByText('#1')).toBeDefined();
    expect(screen.getByText('#2')).toBeDefined();

    // Verify metadata diagnostics block
    expect(screen.getByText('REQ-TST123')).toBeDefined();
    expect(screen.getAllByText('xgboost-v1.0-test').length).toBeGreaterThan(0);
    expect(screen.getByText('v1.0-test')).toBeDefined();
  });

  it('updates selected user profile and triggers ranking reload', async () => {
    render(<App />);

    // Wait for initial render
    await waitFor(() => {
      expect(screen.getByText('Test High-Yield Term Deposit')).toBeDefined();
    });

    expect(screen.getByText(`Account ID: ${mockUsers[0].user_id}`)).toBeDefined();

    // Click on the second user profile
    const secondUserBtn = screen.getByText(new RegExp(mockUsers[1].user_id));
    fireEvent.click(secondUserBtn);

    // Verify view updates and shows new active account ID
    await waitFor(() => {
      expect(screen.getByText(`Account ID: ${mockUsers[1].user_id}`)).toBeDefined();
    });

    // Verify rankOffers was called with the second user's ID
    expect(rankOffersSpy).toHaveBeenCalledWith(mockUsers[1].user_id, true);
  });

  it('interacts with API mode selector (Live Backend vs Mock Mode)', async () => {
    render(<App />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Test High-Yield Term Deposit')).toBeDefined();
    });

    // Locate mode toggle buttons
    const liveBtn = screen.getByRole('button', { name: 'Live Backend' });
    const mockBtn = screen.getByRole('button', { name: 'Mock Mode' });

    // Click "Live Backend"
    fireEvent.click(liveBtn);

    // Verify setMode called with true
    expect(setModeSpy).toHaveBeenCalledWith(true);

    // Click "Mock Mode"
    fireEvent.click(mockBtn);

    // Verify setMode called with false
    expect(setModeSpy).toHaveBeenCalledWith(false);
  });

  it('refreshes the ranking data when "Refresh Rank" is clicked', async () => {
    render(<App />);

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('Test High-Yield Term Deposit')).toBeDefined();
    });

    // Click Refresh Rank
    const refreshBtn = screen.getByRole('button', { name: /Refresh Rank/ });
    fireEvent.click(refreshBtn);

    // Verify it triggers checkHealth and rankOffers again
    await waitFor(() => {
      expect(rankOffersSpy).toHaveBeenCalledTimes(2); // 1 on mount + 1 on refresh
      expect(checkHealthSpy).toHaveBeenCalledTimes(2); // 1 on mount + 1 on refresh
    });
  });

  it('submits feedback actions correctly and displays them in the audit stream', async () => {
    render(<App />);

    // Wait for offers to load
    await waitFor(() => {
      expect(screen.getByText('Test High-Yield Term Deposit')).toBeDefined();
    });

    // Locate Accept Offer button for the top rank offer
    const acceptBtns = screen.getAllByRole('button', { name: /Accept Offer/ });
    expect(acceptBtns.length).toBe(2);

    // Click Accept Offer on the first item
    fireEvent.click(acceptBtns[0]);

    // Verify submitFeedback is called with correct parameters
    expect(submitFeedbackSpy).toHaveBeenCalledWith({
      request_id: 'REQ-TST123',
      user_id: mockUsers[0].user_id,
      offer_id: 'OFR-001',
      action_type: 'accepted',
      rank_position: 1,
      score: 0.92,
      model_version: 'xgboost-v1.0-test',
      timestamp: expect.any(String),
    });

    // Verify it is logged in the Feedback Audit Stream
    await waitFor(() => {
      expect(screen.getByText('ACCEPTED')).toBeDefined();
      expect(screen.getAllByText('Test High-Yield Term Deposit').length).toBeGreaterThan(1);
      expect(screen.getByText(/Event: EVT-TST999/)).toBeDefined();
    });

    // Click View Details on the second item
    const viewDetailBtns = screen.getAllByRole('button', { name: /View Details/ });
    fireEvent.click(viewDetailBtns[1]);

    // Verify submitFeedback for 'clicked' action
    expect(submitFeedbackSpy).toHaveBeenCalledWith({
      request_id: 'REQ-TST123',
      user_id: mockUsers[0].user_id,
      offer_id: 'OFR-002',
      action_type: 'clicked',
      rank_position: 2,
      score: 0.81,
      model_version: 'xgboost-v1.0-test',
      timestamp: expect.any(String),
    });

    // Verify click event is logged in stream
    await waitFor(() => {
      expect(screen.getByText('CLICKED')).toBeDefined();
      expect(screen.getAllByText('Test Savings Rate Boost').length).toBeGreaterThan(1);
    });
  });
});
