import { useState, useEffect } from 'react';
import { 
  User, 
  Briefcase, 
  Calendar, 
  ShieldCheck, 
  CheckCircle, 
  RefreshCw, 
  Sparkles, 
  Sliders, 
  Info, 
  Database, 
  ThumbsUp, 
  Heart, 
  XCircle,
  HelpCircle,
  TrendingUp,
  Award,
  AlertTriangle,
  Flame,
  BookOpen
} from 'lucide-react';
import { apiClient, getCategoryDisplay, getEligibilityNotes, MOCK_OFFERS } from './api/client';
import type { UserProfile, RankedOffer, RankResponse, HealthResponse } from './api/client';

function App() {
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string>('');
  const [rankingData, setRankingData] = useState<RankResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [liveMode, setLiveMode] = useState<boolean>(false);
  const [healthStatus, setHealthStatus] = useState<HealthResponse | null>(null);
  const [showDiagnostics, setShowDiagnostics] = useState<boolean>(true);
  const [feedbackHistory, setFeedbackHistory] = useState<Array<{
    timestamp: string;
    offerTitle: string;
    action: string;
    eventId: string;
  }>>([]);
  const [apiError, setApiError] = useState<string | null>(null);

  // Derive selected user from state
  const selectedUser = users.find(u => u.user_id === selectedUserId) || null;

  // Check backend availability on mount
  useEffect(() => {
    async function detectBackend() {
      try {
        const isHealthy = await apiClient.probeBackend();
        if (isHealthy) {
          setLiveMode(true);
          apiClient.setMode(true);
        } else {
          setLiveMode(false);
          apiClient.setMode(false);
        }
      } catch {
        setLiveMode(false);
        apiClient.setMode(false);
      }
    }
    detectBackend();
  }, []);

  // Fetch health and users when mode changes
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        apiClient.setMode(liveMode);
        
        const health = await apiClient.checkHealth();
        setHealthStatus(health);
        
        const fetchedUsers = await apiClient.getSampleUsers();
        setUsers(fetchedUsers);
        
        if (fetchedUsers.length > 0) {
          if (!fetchedUsers.some(u => u.user_id === selectedUserId)) {
            setSelectedUserId(fetchedUsers[0].user_id);
          }
        } else {
          setSelectedUserId('');
        }
      } catch (err: unknown) {
        setApiError("Initialization/Load failed: " + (err as Error).message);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [liveMode]);

  // Fetch ranking when selected user changes
  useEffect(() => {
    if (!selectedUserId) return;

    async function fetchRanking() {
      try {
        setLoading(true);
        setApiError(null);
        const rankResponse = await apiClient.rankOffers(selectedUserId, true);
        setRankingData(rankResponse);
      } catch (err: unknown) {
        setApiError("Ranking failed: " + (err as Error).message);
        setRankingData(null);
      } finally {
        setLoading(false);
      }
    }
    fetchRanking();
  }, [selectedUserId, liveMode]);

  // Refresh ranking
  const handleRefresh = async () => {
    if (!selectedUserId) return;
    try {
      setLoading(true);
      setApiError(null);
      const rankResponse = await apiClient.rankOffers(selectedUserId, true);
      setRankingData(rankResponse);
      
      // Also refresh health check
      const health = await apiClient.checkHealth();
      setHealthStatus(health);
    } catch (err: unknown) {
      setApiError("Refresh failed: " + (err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Submit offer feedback
  const handleFeedback = async (
    offerId: string, 
    actionType: 'clicked' | 'accepted' | 'dismissed' | 'not_interested', 
    item: RankedOffer
  ) => {
    if (!selectedUser || !rankingData) return;

    try {
      const result = await apiClient.submitFeedback({
        request_id: rankingData.request_id,
        user_id: selectedUser.user_id,
        offer_id: offerId,
        action_type: actionType,
        rank_position: item.rank,
        score: item.model_score,
        model_version: item.model_version,
        timestamp: new Date().toISOString()
      });

      if (result.success) {
        // Add to history list
        setFeedbackHistory(prev => [
          {
            timestamp: new Date().toLocaleTimeString(),
            offerTitle: item.title,
            action: actionType.toUpperCase().replace('_', ' '),
            eventId: result.event_id
          },
          ...prev
        ]);
      }
    } catch (err: unknown) {
      alert(`Feedback submission failed: ${(err as Error).message}`);
    }
  };

  // Helper to fetch matching offer description and category
  const getOfferMeta = (offerId: string) => {
    const mockOffer = MOCK_OFFERS.find(o => o.offer_id === offerId);
    return {
      description: mockOffer?.description || "Specialized banking offer designed for your profile.",
      category: mockOffer?.category || "savings"
    };
  };

  // Get Action Style for visual history
  const getActionBadgeColor = (action: string) => {
    switch (action) {
      case 'ACCEPTED': return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'CLICKED': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'DISMISSED': return 'bg-slate-100 text-slate-800 border-slate-200';
      case 'NOT INTERESTED': return 'bg-rose-100 text-rose-800 border-rose-200';
      default: return 'bg-slate-100 text-slate-800';
    }
  };

  // Get offer category styles
  const getCategoryStyle = (category: string) => {
    switch (category) {
      case 'Savings': return 'bg-emerald-50 text-emerald-700 border-emerald-100';
      case 'Credit Cards': return 'bg-amber-50 text-amber-700 border-amber-100';
      case 'Lending': return 'bg-rose-50 text-rose-700 border-rose-100';
      case 'Advisory': return 'bg-purple-50 text-purple-700 border-purple-100';
      default: return 'bg-slate-50 text-slate-700 border-slate-100';
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* ================= HEADER / APP SHELL ================= */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-600 text-white p-2 rounded-lg shadow-md flex items-center justify-center">
              <TrendingUp className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900 m-0 leading-tight">
                NovaBank Offer Feed
              </h1>
              <span className="text-xs font-medium text-slate-500">
                Real-Time ML Personalization & Ranking Engine (Wave 4 - Feed & Feedback)
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Status indicators */}
            <div className="hidden md:flex items-center space-x-3 px-3 py-1.5 bg-slate-50 rounded-full border border-slate-200 text-xs">
              <span className="flex items-center space-x-1 font-semibold text-slate-600">
                <Database className="h-3 w-3 text-slate-400" />
                <span>Backend:</span>
              </span>
              <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${
                healthStatus?.status === 'ok' && liveMode
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-amber-50 text-amber-700'
              }`}>
                {healthStatus?.status === 'ok' && liveMode ? 'LIVE' : 'MOCKED'}
              </span>
              <span className="w-1.5 h-1.5 bg-slate-300 rounded-full"></span>
              <span className="flex items-center space-x-1 font-semibold text-slate-600">
                <Sparkles className="h-3 w-3 text-indigo-400" />
                <span>Model:</span>
              </span>
              <span className="text-indigo-700 font-semibold">
                {rankingData?.model_version || 'N/A'}
              </span>
            </div>

            {/* ML Architecture docs link */}
            <a
              href="/docs/ml_architecture.html"
              target="_blank"
              rel="noopener noreferrer"
              title="Open ML Architecture &amp; Design documentation"
              className="hidden sm:inline-flex items-center px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-bold text-slate-700 bg-white hover:bg-slate-50 active:bg-slate-100 hover:border-blue-300 hover:text-blue-700 transition-colors shadow-sm cursor-pointer"
            >
              <BookOpen className="h-3.5 w-3.5 mr-1.5 text-blue-600" />
              ML Architecture
            </a>

            {/* Mode switch */}
            <div className="flex items-center bg-slate-100 rounded-lg p-1 border border-slate-200">
              <button
                onClick={() => setLiveMode(false)}
                className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${
                  !liveMode 
                    ? 'bg-white text-slate-950 shadow-sm' 
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Mock Mode
              </button>
              <button
                onClick={() => setLiveMode(true)}
                className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${
                  liveMode 
                    ? 'bg-blue-600 text-white shadow-sm' 
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Live Backend
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* ================= MAIN CONTENT ================= */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col lg:flex-row gap-8">
        
        {/* ================= LEFT COLUMN: CUSTOMER SELECTOR ================= */}
        <section className="w-full lg:w-80 flex flex-col space-y-6 shrink-0">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                <User className="h-4 w-4 text-blue-600" />
                <span>Demographic Selector</span>
              </h2>
              <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                {users.length} Profiles
              </span>
            </div>
            
            <p className="text-xs text-slate-500 mb-4 leading-relaxed">
              Select a synthetic customer profile sourced from UCI Bank Marketing distribution to compute real-time eligible offers & ranking.
            </p>

            {loading && users.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-5 w-5 animate-spin text-blue-600" />
              </div>
            ) : (
              <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
                {users.map((user) => {
                  const isSelected = user.user_id === selectedUserId;
                  return (
                    <button
                      key={user.user_id}
                      onClick={() => setSelectedUserId(user.user_id)}
                      className={`w-full text-left p-3 rounded-lg border transition-all flex items-center justify-between ${
                        isSelected
                          ? 'border-blue-500 bg-blue-50/50 shadow-sm ring-1 ring-blue-500/30'
                          : 'border-slate-150 hover:border-slate-300 bg-white hover:bg-slate-50/80'
                      }`}
                    >
                      <div className="flex flex-col">
                        <span className={`text-sm font-bold ${isSelected ? 'text-blue-900' : 'text-slate-800'}`}>
                          {user.user_id} <span className="font-medium text-slate-400">({user.age} y/o)</span>
                        </span>
                        <span className="text-xs text-slate-500 capitalize">
                          {user.job.replace('.', ' ')} • {user.education.replace('.', ' ')}
                        </span>
                      </div>
                      <span className={`text-[10px] uppercase tracking-wide font-bold px-1.5 py-0.5 rounded ${
                        isSelected 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-slate-100 text-slate-600'
                      }`}>
                        View
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Feedback audit stream */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex-1">
            <h2 className="text-base font-bold text-slate-900 mb-3 flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-emerald-600" />
              <span>Feedback Audit Stream</span>
            </h2>
            <p className="text-xs text-slate-500 mb-4 leading-relaxed font-normal">
              Submitting an action triggers feedback capturing, logged under <code>POST /api/v1/feedback</code> for telemetry and retraining.
            </p>

            {feedbackHistory.length === 0 ? (
              <div className="h-32 border-2 border-dashed border-slate-200 rounded-lg flex flex-col items-center justify-center text-center p-4">
                <HelpCircle className="h-6 w-6 text-slate-300 mb-1" />
                <p className="text-xs text-slate-400 font-medium">No actions submitted yet</p>
                <p className="text-[10px] text-slate-300 mt-0.5">Click actions on the ranked feed below</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
                {feedbackHistory.map((item, idx) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-slate-50 border border-slate-150 text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border tracking-wider ${getActionBadgeColor(item.action)}`}>
                        {item.action}
                      </span>
                      <span className="text-[10px] text-slate-400 font-medium">{item.timestamp}</span>
                    </div>
                    <p className="font-bold text-slate-800 line-clamp-1 mb-0.5">{item.offerTitle}</p>
                    <p className="text-[9px] text-slate-400 font-mono font-medium truncate">Event: {item.eventId}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* ================= RIGHT COLUMN: MAIN WORKSPACE ================= */}
        <section className="flex-1 flex flex-col space-y-6">
          
          {/* Selected Customer Card Details */}
          {selectedUser && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 h-24 w-24 bg-blue-50 rounded-bl-full -z-10 flex items-start justify-end p-4">
                <User className="h-8 w-8 text-blue-100" />
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
                <div>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 mb-1">
                    Customer Profile Active
                  </span>
                  <h2 className="text-xl font-black text-slate-900 flex items-center space-x-2 m-0">
                    <span>Account ID: {selectedUser.user_id}</span>
                  </h2>
                </div>
                
                <button
                  onClick={handleRefresh}
                  disabled={loading}
                  className="inline-flex items-center justify-center px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-bold text-slate-700 bg-white hover:bg-slate-50 active:bg-slate-100 transition-colors shadow-sm cursor-pointer disabled:opacity-50 shrink-0"
                >
                  <RefreshCw className={`h-3 w-3 mr-1.5 ${loading ? 'animate-spin' : ''}`} />
                  Refresh Rank
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-y-4 gap-x-6 bg-slate-50 p-4 rounded-lg border border-slate-100">
                <div className="flex items-start space-x-2">
                  <Calendar className="h-4 w-4 text-slate-400 mt-0.5 shrink-0" />
                  <div>
                    <span className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Demographics</span>
                    <span className="text-xs font-bold text-slate-800 capitalize">Age {selectedUser.age} • {selectedUser.marital}</span>
                  </div>
                </div>

                <div className="flex items-start space-x-2">
                  <Briefcase className="h-4 w-4 text-slate-400 mt-0.5 shrink-0" />
                  <div>
                    <span className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Profession</span>
                    <span className="text-xs font-bold text-slate-800 capitalize truncate block max-w-[130px]" title={selectedUser.job}>
                      {selectedUser.job.replace('.', ' ')}
                    </span>
                  </div>
                </div>

                <div className="flex items-start space-x-2">
                  <Award className="h-4 w-4 text-slate-400 mt-0.5 shrink-0" />
                  <div>
                    <span className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Education</span>
                    <span className="text-xs font-bold text-slate-800 capitalize truncate block max-w-[130px]" title={selectedUser.education}>
                      {selectedUser.education.replace('.', ' ')}
                    </span>
                  </div>
                </div>

                <div className="flex items-start space-x-2">
                  <ShieldCheck className="h-4 w-4 text-slate-400 mt-0.5 shrink-0" />
                  <div>
                    <span className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Default / Loans</span>
                    <span className="text-xs font-bold text-slate-800">
                      Def: <span className="capitalize">{selectedUser.default}</span> • Housing: <span className="capitalize">{selectedUser.housing}</span>
                    </span>
                  </div>
                </div>
              </div>

              {/* Technical UCI specific parameters if expanded */}
              <div className="mt-3 flex items-center justify-between text-[10px] text-slate-400 border-t border-slate-100 pt-3">
                <span>UCI Campaigns: <strong className="text-slate-600">{selectedUser.campaign} calls</strong></span>
                <span>Last Outcome: <strong className={`capitalize ${selectedUser.poutcome === 'success' ? 'text-emerald-600 font-bold' : 'text-slate-600'}`}>{selectedUser.poutcome}</strong></span>
                <span>Macro Rate (Euribor3m): <strong className="text-slate-600">{selectedUser.euribor3m || 'N/A'}%</strong></span>
              </div>
            </div>
          )}

          {/* ================= EXPERIENTIAL FEED RESULTS VIEW ================= */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-black text-slate-900 flex items-center space-x-2 m-0">
                  <Sparkles className="h-5 w-5 text-indigo-500" />
                  <span>Ranked Offer Feed Recommendation</span>
                </h3>
                <p className="text-xs text-slate-500">
                  Pointwise ML scores sorted descending and modified by eligibility logic.
                </p>
              </div>

              <button
                onClick={() => setShowDiagnostics(!showDiagnostics)}
                className={`inline-flex items-center px-2.5 py-1.5 rounded-lg text-xs font-semibold border transition-all cursor-pointer ${
                  showDiagnostics 
                    ? 'bg-indigo-50 border-indigo-200 text-indigo-700 hover:bg-indigo-100' 
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Sliders className="h-3.5 w-3.5 mr-1.5" />
                {showDiagnostics ? 'Hide Diagnostics' : 'Show Diagnostics'}
              </button>
            </div>

            {apiError && (
              <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg flex items-start space-x-2 text-xs">
                <AlertTriangle className="h-4 w-4 text-rose-500 mt-0.5 shrink-0" />
                <div>
                  <span className="font-bold block mb-0.5">API Server Interaction Error</span>
                  <p>{apiError}</p>
                </div>
              </div>
            )}

            {loading && !rankingData ? (
              <div className="bg-white border border-slate-200 rounded-xl py-16 flex flex-col items-center justify-center space-y-3">
                <RefreshCw className="h-8 w-8 text-blue-600 animate-spin" />
                <p className="text-sm font-semibold text-slate-600">Executing machine learning inference...</p>
                <p className="text-xs text-slate-400">Filtering candidates, assembling features, evaluating models</p>
              </div>
            ) : rankingData && rankingData.results.length === 0 ? (
              <div className="bg-white border border-slate-200 rounded-xl py-12 text-center p-6 flex flex-col items-center justify-center">
                <XCircle className="h-10 w-10 text-slate-300 mb-2" />
                <h4 className="text-sm font-bold text-slate-700">No Eligible Offers Available</h4>
                <p className="text-xs text-slate-400 max-w-sm mt-1">
                  This user doesn't meet eligibility requirements for any current synthetic offers in the catalog.
                </p>
              </div>
            ) : rankingData ? (
              <div className="space-y-4">
                {rankingData.results.map((item) => {
                  const meta = getOfferMeta(item.offer_id);
                  const displayCategory = getCategoryDisplay(meta.category);

                  return (
                    <div 
                      key={item.offer_id}
                      className="bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md transition-all p-5 flex flex-col md:flex-row gap-5 relative overflow-hidden"
                    >
                      {/* Ribbon banner for top rank */}
                      {item.rank === 1 && (
                        <div className="absolute top-0 left-0 h-10 w-10 overflow-hidden">
                          <div className="bg-amber-500 text-white text-[8px] font-black uppercase text-center rotate-[-45deg] py-1 w-[60px] absolute top-[5px] left-[-18px] shadow-sm flex items-center justify-center">
                            <Flame className="h-2 w-2 mr-0.5 fill-white" /> TOP
                          </div>
                        </div>
                      )}

                      {/* Rank Position Graphic */}
                      <div className="flex md:flex-col items-center justify-center shrink-0 bg-slate-50 border border-slate-100 rounded-lg p-3 md:w-16 h-12 md:h-20 text-center">
                        <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest md:mb-1 block">RANK</span>
                        <span className={`text-xl font-black ${
                          item.rank === 1 ? 'text-amber-500' : item.rank === 2 ? 'text-slate-500' : 'text-slate-400'
                        }`}>
                          #{item.rank}
                        </span>
                      </div>

                      {/* Offer Details */}
                      <div className="flex-1 space-y-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold border ${getCategoryStyle(displayCategory)}`}>
                            {displayCategory}
                          </span>
                          <span className="text-[10px] font-semibold text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
                            ID: {item.offer_id}
                          </span>
                        </div>

                        <div>
                          <h4 className="text-base font-extrabold text-slate-900 leading-snug">
                            {item.title}
                          </h4>
                          <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                            {meta.description}
                          </p>
                        </div>

                        {/* ML Explanation Panel */}
                        <div className="bg-blue-50/40 border border-blue-100/50 rounded-lg p-3 flex items-start space-x-2 text-xs">
                          <Info className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />
                          <div>
                            <span className="font-bold text-blue-900 block mb-0.5">Why am I seeing this?</span>
                            <p className="text-blue-800 leading-relaxed font-medium">{item.explanation}</p>
                          </div>
                        </div>

                        {/* Diagnostics Expand Area */}
                        {showDiagnostics && (
                          <div className="bg-slate-50 border border-slate-150 rounded-lg p-3 text-[11px] font-mono grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-600">
                            <div>
                              <span className="font-semibold block text-[10px] text-slate-400 uppercase font-sans tracking-wide">Eligibility Check</span>
                              <span className="text-slate-700 block truncate" title={selectedUser ? getEligibilityNotes(selectedUser, item.offer_id) : 'Active Rule (age >= 18)'}>
                                {selectedUser ? getEligibilityNotes(selectedUser, item.offer_id) : 'Active Rule (age >= 18)'}
                              </span>
                            </div>
                            <div>
                              <span className="font-semibold block text-[10px] text-slate-400 uppercase font-sans tracking-wide">Model Score Matrix</span>
                              <span className="text-slate-700 font-bold block">
                                Raw Score: <span className="text-indigo-600">{(item.rerank_factors?.priority_boost ? item.model_score - item.rerank_factors.priority_boost : item.model_score).toFixed(4)}</span> 
                                {item.rerank_factors?.priority_boost ? ` (Priority Adj: +${item.rerank_factors.priority_boost})` : ''}
                                {` | Final: ${item.model_score.toFixed(4)}`}
                              </span>
                              <span className="text-[10px] text-slate-400 block mt-0.5">
                                Normalized: {(item.normalized_score).toFixed(4)}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Action Panel */}
                      <div className="flex md:flex-col justify-center items-stretch gap-2 shrink-0 md:w-36 pt-2 md:pt-0 border-t border-slate-100 md:border-t-0 md:border-l md:pl-5">
                        <button
                          onClick={() => handleFeedback(item.offer_id, 'accepted', item)}
                          className="flex-1 inline-flex items-center justify-center bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white font-bold py-1.5 px-3 rounded-lg text-xs transition-colors shadow-sm cursor-pointer"
                        >
                          <Heart className="h-3 w-3 mr-1 fill-white" /> Accept Offer
                        </button>
                        
                        <button
                          onClick={() => handleFeedback(item.offer_id, 'clicked', item)}
                          className="flex-1 inline-flex items-center justify-center bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-bold py-1.5 px-3 rounded-lg text-xs transition-colors shadow-sm cursor-pointer"
                        >
                          <ThumbsUp className="h-3 w-3 mr-1" /> View Details
                        </button>

                        <div className="flex gap-2">
                          <button
                            onClick={() => handleFeedback(item.offer_id, 'dismissed', item)}
                            title="Dismiss/Hide"
                            className="flex-1 inline-flex items-center justify-center bg-slate-100 hover:bg-slate-200 active:bg-slate-300 text-slate-600 font-bold py-1 px-2 rounded-lg text-xs transition-colors cursor-pointer border border-slate-200"
                          >
                            Dismiss
                          </button>
                          <button
                            onClick={() => handleFeedback(item.offer_id, 'not_interested', item)}
                            title="Not Interested"
                            className="flex-1 inline-flex items-center justify-center bg-rose-50 hover:bg-rose-100 active:bg-rose-200 text-rose-600 font-bold py-1 px-2 rounded-lg text-xs transition-colors cursor-pointer border border-rose-150"
                          >
                            No Thanks
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="bg-white border border-slate-200 rounded-xl py-12 text-center p-6 text-slate-400 text-xs">
                Select a customer profile to view offer rankings
              </div>
            )}

            {/* General API diagnostics block */}
            {showDiagnostics && rankingData && (
              <div className="bg-slate-900 text-slate-300 border border-slate-800 rounded-xl p-4 font-mono text-[11px] space-y-2 shadow-inner">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2">
                  <span className="font-sans font-bold text-slate-400 uppercase tracking-wide text-[10px]">API Response Metadata (POST /api/v1/rank)</span>
                  <span className="bg-indigo-900/50 text-indigo-300 border border-indigo-800/50 rounded px-1.5 py-0.5 text-[9px] font-bold">Inference OK</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1">
                  <div>Request ID: <span className="text-white font-bold">{rankingData.request_id}</span></div>
                  <div>Generated At: <span className="text-slate-400">{new Date(rankingData.generated_at).toLocaleString()}</span></div>
                  <div>Model Version: <span className="text-indigo-400 font-bold">{rankingData.model_version}</span></div>
                  <div>Feature Version: <span className="text-emerald-400 font-bold">{rankingData.feature_version}</span></div>
                </div>
              </div>
            )}
          </div>
        </section>

      </main>

      {/* ================= FOOTER / APP SHELL ================= */}
      <footer className="bg-white border-t border-slate-200 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs text-slate-500 font-medium">
          <p>© 2026 NovaBank AI Systems. Sourced from the UCI Bank Marketing Dataset (CC BY 4.0).</p>
          <p className="mt-1 text-slate-400 font-normal">
            This module is part of the Bank Offer Feed Ranking monorepo. Built for Wave 4, (T-030 - T-034 Live Feed & Feedback Loops).
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
