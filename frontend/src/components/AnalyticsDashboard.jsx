import React, { useState, useEffect } from 'react';
import axios from 'axios';

const AnalyticsDashboard = ({ userId, userEmail }) => {
  const [activeTab, setActiveTab] = useState('trends');
  const [stressTrends, setStressTrends] = useState(null);
  const [emotionDist, setEmotionDist] = useState(null);
  const [insights, setInsights] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [days, setDays] = useState(30);

  useEffect(() => {
    if (userId) {
      fetchAnalytics();
    }
  }, [userId, days]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      
      const [trendsRes, emotionsRes, insightsRes, recsRes, predictRes] = await Promise.all([
        axios.get(`/api/analytics/stress-trends?user_id=${userId}&days=${days}`, { headers }),
        axios.get(`/api/analytics/emotion-distribution?user_id=${userId}&days=${days}`, { headers }),
        axios.get(`/api/analytics/insights?user_id=${userId}`, { headers }),
        axios.get(`/api/recommendations/personalized?user_id=${userId}&limit=5`, { headers }),
        axios.get(`/api/predict/stress-level?user_id=${userId}&hours_ahead=24`, { headers })
      ]);

      setStressTrends(trendsRes.data);
      setEmotionDist(emotionsRes.data);
      setInsights(insightsRes.data);
      setRecommendations(recsRes.data);
      setPredictions(predictRes.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
    setLoading(false);
  };

  const getStressLevel = (score) => {
    if (score < 30) return { label: 'Low', color: 'bg-green-500' };
    if (score < 60) return { label: 'Moderate', color: 'bg-yellow-500' };
    if (score < 80) return { label: 'High', color: 'bg-orange-500' };
    return { label: 'Critical', color: 'bg-red-500' };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">Stress Analytics Dashboard</h1>
          <p className="text-slate-600">Comprehensive insights into your stress patterns and wellness</p>
        </div>

        {/* Time Range Selector */}
        <div className="mb-6 flex gap-2">
          {[7, 14, 30, 60, 90].map(d => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                days === d
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50'
              }`}
            >
              {d}D
            </button>
          ))}
        </div>

        {/* Navigation Tabs */}
        <div className="flex gap-2 mb-6 border-b border-slate-300">
          {['trends', 'emotions', 'insights', 'recommendations', 'predictions'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 font-medium transition border-b-2 ${
                activeTab === tab
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <p className="mt-4 text-slate-600">Loading analytics...</p>
          </div>
        )}

        {!loading && (
          <>
            {/* Stress Trends Tab */}
            {activeTab === 'trends' && stressTrends && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <p className="text-slate-600 text-sm font-medium mb-2">Average Stress</p>
                    <div className="flex items-end gap-2">
                      <span className="text-3xl font-bold text-slate-900">{stressTrends.average_stress}</span>
                      <span className={`text-sm font-semibold px-2 py-1 rounded ${getStressLevel(stressTrends.average_stress).color} text-white`}>
                        {getStressLevel(stressTrends.average_stress).label}
                      </span>
                    </div>
                  </div>
                  
                  <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <p className="text-slate-600 text-sm font-medium mb-2">Range</p>
                    <p className="text-sm text-slate-700 mb-1">Min: <span className="font-bold">{stressTrends.stress_range.min}</span></p>
                    <p className="text-sm text-slate-700">Max: <span className="font-bold">{stressTrends.stress_range.max}</span></p>
                  </div>

                  <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <p className="text-slate-600 text-sm font-medium mb-2">Total Sessions</p>
                    <p className="text-3xl font-bold text-slate-900">{stressTrends.total_sessions}</p>
                  </div>
                </div>

                {/* Trend Chart */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                  <h3 className="text-lg font-semibold text-slate-900 mb-4">Stress Trend</h3>
                  <div className="space-y-2 max-h-80 overflow-y-auto">
                    {stressTrends.trend.map((day, idx) => (
                      <div key={idx} className="flex items-center gap-3">
                        <span className="text-xs text-slate-600 min-w-24">{day.date}</span>
                        <div className="flex-1 bg-slate-200 rounded-full h-6">
                          <div
                            className={`h-full rounded-full ${getStressLevel(day.average_stress).color} transition-all`}
                            style={{ width: `${day.average_stress}%` }}
                          />
                        </div>
                        <span className="text-sm font-semibold text-slate-900 min-w-12 text-right">{day.average_stress}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Emotions Tab */}
            {activeTab === 'emotions' && emotionDist && (
              <div className="space-y-6">
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                  <h3 className="text-lg font-semibold text-slate-900 mb-4">Emotion Distribution</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      {Object.entries(emotionDist.emotions || {}).map(([emotion, percentage]) => (
                        <div key={emotion}>
                          <div className="flex justify-between mb-1">
                            <span className="text-sm font-medium text-slate-700">{emotion}</span>
                            <span className="text-sm font-semibold text-slate-900">{percentage}%</span>
                          </div>
                          <div className="w-full bg-slate-200 rounded-full h-2">
                            <div
                              className="bg-indigo-600 h-2 rounded-full"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="flex flex-col justify-center items-center bg-slate-50 rounded-lg p-4">
                      <p className="text-sm text-slate-600 mb-2">Dominant Emotion</p>
                      <p className="text-2xl font-bold text-indigo-600">{emotionDist.dominant_emotion}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Insights Tab */}
            {activeTab === 'insights' && insights && (
              <div className="space-y-4">
                {insights.insights.map((insight, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-xl border ${
                      insight.type === 'warning'
                        ? 'bg-red-50 border-red-200'
                        : insight.type === 'positive'
                        ? 'bg-green-50 border-green-200'
                        : insight.type === 'insight'
                        ? 'bg-blue-50 border-blue-200'
                        : 'bg-yellow-50 border-yellow-200'
                    }`}
                  >
                    <p className={`font-semibold ${
                      insight.type === 'warning'
                        ? 'text-red-900'
                        : insight.type === 'positive'
                        ? 'text-green-900'
                        : insight.type === 'insight'
                        ? 'text-blue-900'
                        : 'text-yellow-900'
                    }`}>
                      {insight.message}
                    </p>
                  </div>
                ))}
              </div>
            )}

            {/* Recommendations Tab */}
            {activeTab === 'recommendations' && recommendations && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {recommendations.recommendations.map((rec, idx) => (
                  <div key={idx} className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 hover:shadow-md transition">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-slate-900 text-lg">{rec.title}</h4>
                      <span className="text-sm px-2 py-1 bg-indigo-100 text-indigo-700 rounded">{rec.category}</span>
                    </div>
                    <p className="text-slate-600 text-sm mb-3">{rec.description}</p>
                    <div className="flex gap-4 text-xs text-slate-600">
                      <span>⏱️ {rec.duration_minutes} min</span>
                      <span>📊 {rec.effectiveness_score * 100}% effective</span>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Predictions Tab */}
            {activeTab === 'predictions' && predictions && (
              <div className="space-y-6">
                <div className="bg-gradient-to-br from-indigo-50 to-blue-50 p-8 rounded-xl border border-indigo-200">
                  <h3 className="text-lg font-semibold text-slate-900 mb-4">24-Hour Stress Prediction</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <p className="text-slate-600 text-sm mb-2">Predicted Stress Level</p>
                      <div className="flex items-end gap-3">
                        <span className="text-4xl font-bold text-indigo-600">
                          {predictions.prediction?.predicted_stress_score}
                        </span>
                        <span className={`px-3 py-1 rounded-lg ${getStressLevel(predictions.prediction?.predicted_stress_score).color} text-white font-medium`}>
                          {getStressLevel(predictions.prediction?.predicted_stress_score).label}
                        </span>
                      </div>
                    </div>
                    <div>
                      <p className="text-slate-600 text-sm mb-2">Confidence Level</p>
                      <p className="text-2xl font-bold text-indigo-600">{predictions.prediction?.confidence}%</p>
                      <p className="text-sm text-slate-600 mt-2">Trend: <span className="font-semibold capitalize">{predictions.prediction?.trend}</span></p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
