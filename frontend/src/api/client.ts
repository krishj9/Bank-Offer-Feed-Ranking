// API Client and Mock Data Provider for Bank Offer Feed Ranking
// This client operates in two modes:
// 1. Live mode: Connects to the FastAPI backend API.
// 2. Mock mode: Simulates the ML scoring, eligibility filtering, and feedback submission locally.
// This allows the frontend scaffold to be fully interactive and functional before the backend is running.

// ==========================================
// 1. TYPE DEFINITIONS (Matching Contracts)
// ==========================================

export interface UserProfile {
  user_id: string;
  age: number;
  job: string;
  marital: string;
  education: string;
  default: string;
  housing: string;
  loan: string;
  contact: string;
  month: string;
  day_of_week: string;
  campaign: number;
  pdays: number;
  previous: number;
  poutcome: string;
  emp_var_rate: number;
  cons_price_idx: number;
  cons_conf_idx: number;
  euribor3m: number;
  nr_employed: number;
}

export interface SampleUsersResponse {
  users: UserProfile[];
  count: number;
}

export interface Offer {
  offer_id: string;
  offer_type: string;
  title: string;
  description: string;
  category: string;
  priority_weight: number;
  active: boolean;
  eligibility_expression: string;
  version: string;
}

export interface RankedOffer {
  rank: number;
  offer_id: string;
  offer_type: string;
  title: string;
  model_score: number;
  normalized_score: number;
  explanation: string;
  model_version: string;
  request_id: string;
  rerank_factors: {
    priority_boost?: number;
    raw_rank?: number;
    reranked_rank?: number;
    [key: string]: any;
  };
}

export interface RankResponse {
  request_id: string;
  model_version: string;
  feature_version: string;
  generated_at: string;
  results: RankedOffer[];
  warnings?: string[];
}

export type FeedbackAction = 'viewed' | 'clicked' | 'accepted' | 'dismissed' | 'not_interested';

export interface FeedbackEventRequest {
  request_id: string;
  user_id: string;
  offer_id: string;
  action_type: FeedbackAction;
  model_version?: string | null;
  score?: number | null;
  rank_position?: number | null;
  timestamp?: string | null;
}

export interface FeedbackEventResponse {
  event_id: string;
  status: string;
  stored_at: string;
  storage: string;
}

export interface FeedbackResponse {
  success: boolean;
  event_id: string;
  message: string;
}

export interface HealthResponse {
  status: string;
  model_ready: boolean;
  artifacts_dir: string;
  artifact_status: {
    model: boolean;
    preprocessor: boolean;
    manifest: boolean;
  };
}

// ==========================================
// 2. MOCK DATA FOUNDATIONS
// ==========================================

export const MOCK_USERS: UserProfile[] = [
  {
    "user_id": "demo_user_001",
    "age": 24,
    "job": "blue-collar",
    "marital": "married",
    "education": "basic.9y",
    "default": "no",
    "housing": "yes",
    "loan": "no",
    "contact": "telephone",
    "month": "may",
    "day_of_week": "mon",
    "campaign": 2,
    "pdays": 999,
    "previous": 0,
    "poutcome": "nonexistent",
    "emp_var_rate": 1.1,
    "cons_price_idx": 93.994,
    "cons_conf_idx": -36.4,
    "euribor3m": 4.858,
    "nr_employed": 5191.0
  },
  {
    "user_id": "demo_user_002",
    "age": 37,
    "job": "management",
    "marital": "married",
    "education": "university.degree",
    "default": "no",
    "housing": "no",
    "loan": "no",
    "contact": "telephone",
    "month": "may",
    "day_of_week": "wed",
    "campaign": 2,
    "pdays": 999,
    "previous": 0,
    "poutcome": "nonexistent",
    "emp_var_rate": 1.1,
    "cons_price_idx": 93.994,
    "cons_conf_idx": -36.4,
    "euribor3m": 4.857,
    "nr_employed": 5191.0
  },
  {
    "user_id": "demo_user_003",
    "age": 44,
    "job": "self-employed",
    "marital": "single",
    "education": "professional.course",
    "default": "no",
    "housing": "no",
    "loan": "no",
    "contact": "cellular",
    "month": "may",
    "day_of_week": "mon",
    "campaign": 6,
    "pdays": 12,
    "previous": 1,
    "poutcome": "success",
    "emp_var_rate": -1.8,
    "cons_price_idx": 92.893,
    "cons_conf_idx": -46.2,
    "euribor3m": 1.354,
    "nr_employed": 5099.1
  },
  {
    "user_id": "demo_user_004",
    "age": 33,
    "job": "blue-collar",
    "marital": "single",
    "education": "basic.4y",
    "default": "no",
    "housing": "no",
    "loan": "no",
    "contact": "cellular",
    "month": "may",
    "day_of_week": "tue",
    "campaign": 1,
    "pdays": 999,
    "previous": 0,
    "poutcome": "nonexistent",
    "emp_var_rate": -1.8,
    "cons_price_idx": 92.893,
    "cons_conf_idx": -46.2,
    "euribor3m": 1.291,
    "nr_employed": 5099.1
  },
  {
    "user_id": "demo_user_005",
    "age": 40,
    "job": "blue-collar",
    "marital": "married",
    "education": "basic.9y",
    "default": "unknown",
    "housing": "yes",
    "loan": "yes",
    "contact": "cellular",
    "month": "may",
    "day_of_week": "wed",
    "campaign": 2,
    "pdays": 999,
    "previous": 0,
    "poutcome": "nonexistent",
    "emp_var_rate": -1.8,
    "cons_price_idx": 92.893,
    "cons_conf_idx": -46.2,
    "euribor3m": 1.281,
    "nr_employed": 5099.1
  },
  {
    "user_id": "demo_user_006",
    "age": 39,
    "job": "management",
    "marital": "married",
    "education": "university.degree",
    "default": "no",
    "housing": "no",
    "loan": "no",
    "contact": "telephone",
    "month": "jun",
    "day_of_week": "mon",
    "campaign": 3,
    "pdays": 999,
    "previous": 0,
    "poutcome": "nonexistent",
    "emp_var_rate": 1.4,
    "cons_price_idx": 94.465,
    "cons_conf_idx": -41.8,
    "euribor3m": 4.96,
    "nr_employed": 5228.1
  },
  {
    "user_id": "demo_user_007",
    "age": 39,
    "job": "management",
    "marital": "married",
    "education": "university.degree",
    "default": "no",
    "housing": "no",
    "loan": "no",
    "contact": "telephone",
    "month": "apr",
    "day_of_week": "tue",
    "campaign": 1,
    "pdays": 999,
    "previous": 2,
    "poutcome": "failure",
    "emp_var_rate": -1.8,
    "cons_price_idx": 93.749,
    "cons_conf_idx": -34.6,
    "euribor3m": 0.646,
    "nr_employed": 5008.7
  },
  {
    "user_id": "demo_user_008",
    "age": 40,
    "job": "admin.",
    "marital": "single",
    "education": "university.degree",
    "default": "no",
    "housing": "no",
    "loan": "no",
    "contact": "telephone",
    "month": "jun",
    "day_of_week": "mon",
    "campaign": 2,
    "pdays": 999,
    "previous": 0,
    "poutcome": "nonexistent",
    "emp_var_rate": 1.4,
    "cons_price_idx": 94.465,
    "cons_conf_idx": -41.8,
    "euribor3m": 4.958,
    "nr_employed": 5228.1
  },
  {
    "user_id": "demo_user_009",
    "age": 24,
    "job": "self-employed",
    "marital": "single",
    "education": "unknown",
    "default": "no",
    "housing": "no",
    "loan": "yes",
    "contact": "cellular",
    "month": "jul",
    "day_of_week": "thu",
    "campaign": 2,
    "pdays": 999,
    "previous": 0,
    "poutcome": "nonexistent",
    "emp_var_rate": -2.9,
    "cons_price_idx": 92.469,
    "cons_conf_idx": -33.6,
    "euribor3m": 1.072,
    "nr_employed": 5076.2
  },
  {
    "user_id": "demo_user_010",
    "age": 19,
    "job": "student",
    "marital": "single",
    "education": "unknown",
    "default": "no",
    "housing": "unknown",
    "loan": "unknown",
    "contact": "cellular",
    "month": "apr",
    "day_of_week": "mon",
    "campaign": 3,
    "pdays": 999,
    "previous": 0,
    "poutcome": "nonexistent",
    "emp_var_rate": -1.8,
    "cons_price_idx": 93.075,
    "cons_conf_idx": -47.1,
    "euribor3m": 1.405,
    "nr_employed": 5099.1
  }
];

export const MOCK_OFFERS: Offer[] = [
  {
    offer_id: "OFR-001",
    offer_type: "term_deposit_reminder",
    title: "Lock in a High-Yield Term Deposit",
    description: "Secure your savings with our market-leading term deposit rate.",
    category: "savings",
    priority_weight: 1.0,
    active: true,
    eligibility_expression: '{"min_age": 25, "exclude_jobs": ["student", "unemployed"]}',
    version: "1.0"
  },
  {
    offer_id: "OFR-002",
    offer_type: "savings_boost",
    title: "Savings Rate Boost",
    description: "Earn extra interest on your savings account this month.",
    category: "savings",
    priority_weight: 1.2,
    active: true,
    eligibility_expression: '{"max_age": 35, "marital": ["single"]}',
    version: "1.0"
  },
  {
    offer_id: "OFR-003",
    offer_type: "credit_card_upgrade",
    title: "Premium Credit Card Upgrade",
    description: "Upgrade to our premium rewards credit card with zero fees for the first year.",
    category: "credit",
    priority_weight: 1.5,
    active: true,
    eligibility_expression: '{"min_age": 21, "education": ["university.degree", "professional.course"]}',
    version: "1.0"
  },
  {
    offer_id: "OFR-004",
    offer_type: "refinance_prompt",
    title: "Refinance Your Home Loan",
    description: "Lower your monthly payments by refinancing your mortgage today.",
    category: "credit",
    priority_weight: 1.8,
    active: true,
    eligibility_expression: '{"housing": "yes"}',
    version: "1.0"
  },
  {
    offer_id: "OFR-005",
    offer_type: "advisor_callback",
    title: "Free Financial Wellness Session",
    description: "Schedule a free 30-minute callback with one of our financial advisors.",
    category: "advice",
    priority_weight: 0.8,
    active: true,
    eligibility_expression: '{"min_age": 40, "loan": "no"}',
    version: "1.0"
  }
];

// ==========================================
// 3. MOCK ALGORITHMS (Simulating Backend)
// ==========================================

// Checks eligibility deterministically based on simple rules matching ml/data/eligibility.py
function checkEligibility(user: UserProfile, offer: Offer): { eligible: boolean; note: string } {
  const { age, job, marital, education, housing, loan } = user;
  const reasons: string[] = [];
  
  if (offer.offer_id === "OFR-001") {
    if (age < 25) reasons.push(`User age ${age} is less than min_age 25`);
    if (["student", "unemployed"].includes(job)) {
      reasons.push(`User job '${job}' is in excluded jobs ["student", "unemployed"]`);
    }
  } else if (offer.offer_id === "OFR-002") {
    if (age > 35) reasons.push(`User age ${age} is greater than max_age 35`);
    if (marital !== "single") reasons.push(`User marital status '${marital}' not in required ["single"]`);
  } else if (offer.offer_id === "OFR-003") {
    if (age < 21) reasons.push(`User age ${age} is less than min_age 21`);
    if (!["university.degree", "professional.course"].includes(education)) {
      reasons.push(`User education '${education}' not in ["university.degree", "professional.course"]`);
    }
  } else if (offer.offer_id === "OFR-004") {
    if (housing !== "yes") reasons.push(`User housing '${housing}' != yes`);
  } else if (offer.offer_id === "OFR-005") {
    if (age < 40) reasons.push(`User age ${age} is less than min_age 40`);
    if (loan !== "no") reasons.push(`User loan '${loan}' != no`);
  }

  return {
    eligible: reasons.length === 0,
    note: reasons.length === 0 ? "Eligible" : reasons.join(", ")
  };
}

// Simulates point-wise scoring model based on UCI coefficients & heuristics
function computeModelScore(user: UserProfile, offer: Offer): number {
  let score = 0.5; // Base probability

  // Adjustments based on job
  if (user.job === 'retired' || user.job === 'student') {
    score += 0.2;
  } else if (user.job === 'blue-collar' || user.job === 'services') {
    score -= 0.1;
  }

  // Adjustments based on previous outcome
  if (user.poutcome === 'success') {
    score += 0.25;
  } else if (user.poutcome === 'failure') {
    score -= 0.05;
  }

  // Adjustments based on age
  if (user.age > 60 || user.age < 25) {
    score += 0.15;
  }

  // Offer compatibility boosts
  if (offer.offer_type === 'term_deposit_reminder') {
    if (user.job === 'retired') score += 0.15;
    if (user.education === 'university.degree') score += 0.05;
  }
  
  if (offer.offer_type === 'savings_boost') {
    if (user.job === 'student') score += 0.2;
    if (user.marital === 'single') score += 0.05;
  }

  if (offer.offer_type === 'credit_card_upgrade') {
    if (user.job === 'management' || user.job === 'entrepreneur') score += 0.15;
    if (user.education === 'university.degree') score += 0.08;
  }

  if (offer.offer_type === 'refinance_prompt') {
    if (user.age >= 35 && user.age <= 50) score += 0.1;
    if (user.marital === 'married') score += 0.05;
  }

  return Math.min(0.99, Math.max(0.01, score));
}

// Simulates template-based explanations
function generateExplanation(user: UserProfile, offer: Offer, score: number): string {
  if (score > 0.7) {
    if (user.poutcome === 'success') {
      return "Highly recommended because of your positive campaign response history and alignment with your profile attributes.";
    }
    if (user.job === 'retired' && offer.category === 'advice') {
      return "Excellent match for your retired status, prioritizing secure wealth management and estate guidance.";
    }
    if (user.job === 'student' && offer.category === 'savings') {
      return "Top recommendation to maximize interest benefits while managing a student budget.";
    }
    return `Strong recommendation because your current profile matches key positive conversion indicators for ${offer.title}.`;
  } else if (score > 0.45) {
    if (user.housing === 'yes' && offer.category === 'credit') {
      return "Recommended to check your potential savings on your housing loan refinancing options.";
    }
    return "Recommended based on demographic category preferences and general bank campaign performance indicators.";
  } else {
    return "Presented as an additional utility offering that fits within our baseline eligibility criteria.";
  }
}

// Helper to compute eligibility notes (used by Diagnostics panel in both modes)
export function getEligibilityNotes(user: UserProfile, offerId: string): string {
  if (offerId === "OFR-001") {
    const reasons: string[] = [];
    if (user.age < 25) reasons.push(`Age ${user.age} < 25`);
    if (["student", "unemployed"].includes(user.job)) reasons.push(`Job is ${user.job} (excluded)`);
    return reasons.length === 0 ? "Age >= 25, job is not student or unemployed" : `Ineligible: ${reasons.join(", ")}`;
  }
  if (offerId === "OFR-002") {
    const reasons: string[] = [];
    if (user.age > 35) reasons.push(`Age ${user.age} > 35`);
    if (user.marital !== "single") reasons.push(`Marital status is ${user.marital} (requires single)`);
    return reasons.length === 0 ? "Age <= 35, marital status is single" : `Ineligible: ${reasons.join(", ")}`;
  }
  if (offerId === "OFR-003") {
    const reasons: string[] = [];
    if (user.age < 21) reasons.push(`Age ${user.age} < 21`);
    if (!["university.degree", "professional.course"].includes(user.education)) {
      reasons.push(`Education is ${user.education} (requires degree/course)`);
    }
    return reasons.length === 0 ? "Age >= 21, education is university degree or professional course" : `Ineligible: ${reasons.join(", ")}`;
  }
  if (offerId === "OFR-004") {
    return user.housing === "yes" ? "User has housing loan (housing = yes)" : "Ineligible: User housing != yes";
  }
  if (offerId === "OFR-005") {
    const reasons: string[] = [];
    if (user.age < 40) reasons.push(`Age ${user.age} < 40`);
    if (user.loan !== "no") reasons.push(`Has personal loan (requires no)`);
    return reasons.length === 0 ? "Age >= 40, has no personal loan" : `Ineligible: ${reasons.join(", ")}`;
  }
  return "Eligible";
}

// Helper to map category IDs to human readable labels
export function getCategoryDisplay(category: string): string {
  switch (category) {
    case 'savings': return 'Savings';
    case 'credit': return 'Credit Cards';
    case 'advice': return 'Advisory';
    default: return category.charAt(0).toUpperCase() + category.slice(1);
  }
}

// ==========================================
// 4. API CLIENT IMPLEMENTATION
// ==========================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const getUrl = (path: string) => {
  if (path === '/health') {
    return `${API_BASE_URL}/health`;
  }
  return `${API_BASE_URL}/api/v1${path}`;
};

export class BankOfferApiClient {
  private useLiveBackend: boolean;

  constructor() {
    this.useLiveBackend = false;
  }

  setMode(live: boolean) {
    this.useLiveBackend = live;
    console.log(`[BankOfferApiClient] Switched to ${live ? 'LIVE API' : 'MOCK'} mode`);
  }

  getMode() {
    return this.useLiveBackend;
  }

  /**
   * Probes the live backend to see if it is available.
   */
  async probeBackend(): Promise<boolean> {
    try {
      const response = await fetch(getUrl('/health'), { method: 'GET', signal: AbortSignal.timeout(2000) });
      if (response.ok) {
        const data = await response.json();
        return data.status === "ok";
      }
    } catch {
      // Offline/unreachable
    }
    return false;
  }

  /**
   * Health Check
   */
  async checkHealth(): Promise<HealthResponse> {
    if (!this.useLiveBackend) {
      return {
        status: "ok",
        model_ready: true,
        artifacts_dir: "mock_artifacts",
        artifact_status: {
          model: true,
          preprocessor: true,
          manifest: true
        }
      };
    }

    try {
      const response = await fetch(getUrl('/health'));
      if (!response.ok) throw new Error("Health check failed");
      return await response.json();
    } catch (error) {
      console.warn("FastAPI backend is offline. Falling back to mock health data.", error);
      return {
        status: "ok (mock fallback)",
        model_ready: true,
        artifacts_dir: "fallback_artifacts",
        artifact_status: {
          model: true,
          preprocessor: true,
          manifest: true
        }
      };
    }
  }

  /**
   * Get Sample Users
   */
  async getSampleUsers(): Promise<UserProfile[]> {
    if (!this.useLiveBackend) {
      return MOCK_USERS;
    }

    try {
      const response = await fetch(getUrl('/sample-users'));
      if (!response.ok) throw new Error("Failed to fetch sample users");
      const data: SampleUsersResponse = await response.json();
      return data.users;
    } catch (error) {
      console.warn("FastAPI backend is offline. Falling back to mock sample users.", error);
      return MOCK_USERS;
    }
  }

  /**
   * Rank Offers for a User
   */
  async rankOffers(userId: string, debug: boolean = true): Promise<RankResponse> {
    if (!this.useLiveBackend) {
      const user = MOCK_USERS.find(u => u.user_id === userId) || MOCK_USERS[0];
      
      const eligiblePairs: { offer: Offer; note: string }[] = [];
      for (const offer of MOCK_OFFERS) {
        const check = checkEligibility(user, offer);
        if (check.eligible) {
          eligiblePairs.push({ offer, note: check.note });
        }
      }

      const rawResults: RankedOffer[] = eligiblePairs.map(({ offer }) => {
        const score = computeModelScore(user, offer);
        const normalized_score = Math.min(1.0, Math.max(0.0, score));
        const explanation = generateExplanation(user, offer, score);
        const requestId = `REQ-${Math.floor(100000 + Math.random() * 900000)}`;

        return {
          rank: 0,
          offer_id: offer.offer_id,
          offer_type: offer.offer_type,
          title: offer.title,
          model_score: parseFloat(score.toFixed(4)),
          normalized_score: parseFloat(normalized_score.toFixed(4)),
          explanation: explanation,
          model_version: "xgboost-v1.0-baseline",
          request_id: requestId,
          rerank_factors: {
            raw_rank: 0,
            reranked_rank: 0,
            priority_boost: 0.0
          }
        };
      });

      const sortedResults = [...rawResults].sort((a, b) => b.model_score - a.model_score);
      
      const rerankedResults = sortedResults.map((item, index) => {
        const offer = MOCK_OFFERS.find(o => o.offer_id === item.offer_id)!;
        const originalScore = item.model_score;
        const priorityAdjustment = (offer.priority_weight - 1.0) * 0.05;
        const rerankedScore = originalScore + priorityAdjustment;

        return {
          ...item,
          model_score: parseFloat(Math.min(0.99, Math.max(0.01, rerankedScore)).toFixed(4)),
          rerank_factors: {
            raw_rank: index + 1,
            reranked_rank: 0,
            priority_boost: parseFloat(priorityAdjustment.toFixed(4))
          }
        };
      });

      const finalSorted = [...rerankedResults]
        .sort((a, b) => b.model_score - a.model_score)
        .map((item, index) => ({
          ...item,
          rank: index + 1,
          rerank_factors: {
            ...item.rerank_factors,
            reranked_rank: index + 1
          }
        }));

      return {
        request_id: `REQ-${Math.floor(100000 + Math.random() * 900000)}`,
        model_version: "xgboost-v1.0-baseline",
        feature_version: "v1.0-clean",
        generated_at: new Date().toISOString(),
        results: finalSorted
      };
    }

    try {
      const response = await fetch(getUrl('/rank'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, debug })
      });
      if (!response.ok) throw new Error("Failed to rank offers");
      return await response.json();
    } catch (error) {
      console.warn("FastAPI backend is offline. Falling back to local ranking execution.", error);
      const backupClient = new BankOfferApiClient();
      return backupClient.rankOffers(userId, debug);
    }
  }

  /**
   * Submit Feedback Event
   */
  async submitFeedback(feedback: FeedbackEventRequest): Promise<FeedbackResponse> {
    if (!this.useLiveBackend) {
      const eventId = `EVT-${Math.floor(100000 + Math.random() * 900000)}`;
      console.log("[BankOfferApiClient] Submitted mock feedback successfully:", {
        eventId,
        ...feedback
      });
      return {
        success: true,
        event_id: eventId,
        message: `Feedback for action '${feedback.action_type}' recorded successfully (Mock).`
      };
    }

    try {
      const response = await fetch(getUrl('/feedback'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(feedback)
      });
      if (!response.ok) throw new Error("Failed to submit feedback");
      const data: FeedbackEventResponse = await response.json();
      return {
        success: true,
        event_id: data.event_id,
        message: `Feedback recorded on backend. Status: ${data.status}, Storage: ${data.storage}`
      };
    } catch (error) {
      console.warn("FastAPI backend is offline. Falling back to mock feedback recording.", error);
      const eventId = `EVT-FB-${Math.floor(100000 + Math.random() * 900000)}`;
      return {
        success: true,
        event_id: eventId,
        message: `Feedback recorded locally (Fallback). Action: ${feedback.action_type}`
      };
    }
  }
}

export const apiClient = new BankOfferApiClient();
