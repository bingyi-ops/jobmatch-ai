const BASE = '/api';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const isFormData = options?.body instanceof FormData;
  const headers: Record<string, string> = {};
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }
  const res = await fetch(`${BASE}${url}`, {
    ...options,
    headers: { ...headers, ...(options?.headers as Record<string, string>) },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }
  return res.json();
}

export const api = {
  // Jobs
  getAllJobs: (params: Record<string, string | number>) =>
    request<{ items: any[]; total: number; page: number; page_size: number; has_more: boolean }>(
      `/jobs/all?${new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]))}`
    ),

  searchJobs: (q: string, page = 1) =>
    request<{ items: any[]; total: number }>(`/jobs/search?q=${encodeURIComponent(q)}&page=${page}`),

  getJobDetail: (id: number) => request<any>(`/jobs/${id}`),

  getSimilarJobs: (id: number, limit = 5) =>
    request<{ items: any[] }>(`/jobs/${id}/similar?limit=${limit}`),

  getCompanyInfo: (id: number) => request<any>(`/jobs/${id}/company-info`),

  // Featured
  getFeatured: (params: Record<string, string | number>) =>
    request<{ items: any[]; total: number; page: number; today_new: number }>(
      `/featured?${new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]))}`
    ),

  // Applications
  getApplications: (params: Record<string, string | number>) =>
    request<{ items: any[]; total: number }>(
      `/applications?${new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]))}`
    ),

  createApplication: (body: { job_id: number; match_record_id?: number; notes?: any }) =>
    request<any>('/applications', { method: 'POST', body: JSON.stringify(body) }),

  updateApplication: (id: number, body: { status?: string; notes?: any }) =>
    request<any>(`/applications/${id}`, { method: 'PUT', body: JSON.stringify(body) }),

  getAppStats: () => request<any>('/applications/stats'),

  // Resume
  getResumeProfile: () => request<any>('/resume/profile'),

  uploadResume: (file?: File) => {
    const fd = new FormData();
    if (file) fd.append('file', file);
    // FastAPI 需要 field name = 'file'，与后端一致
    return request<any>('/resume/upload', { method: 'POST', body: fd });
  },

  // Feedback
  submitFeedback: (body: { match_record_id: number; action: string; ignore_reason?: string }) =>
    request<any>('/feedback', { method: 'POST', body: JSON.stringify(body) }),

  getFeedbackHistory: (limit = 20) =>
    request<any[]>(`/feedback?limit=${limit}`),

  // Interview Prep & Review
  getInterviewPrep: (jobId: number) => request<any>(`/jobs/${jobId}/interview-prep`),

  startMockInterview: (body: { job_id: number }) =>
    request<any>('/interview/start', { method: 'POST', body: JSON.stringify(body) }),

  evaluateAnswer: (body: { question_id: number; answer: string }) =>
    request<any>('/interview/evaluate', { method: 'POST', body: JSON.stringify(body) }),

  // Interview Review
  submitInterviewReview: (body: {
    job_id: number;
    application_id?: number;
    review_text: string;
    score_self: number;
    questions_asked?: string[];
    difficult_questions?: string;
  }) => request<any>('/interview/review', { method: 'POST', body: JSON.stringify(body) }),

  getInterviewReviews: (jobId?: number) =>
    request<{ reviews: any[] }>(`/interview/review${jobId ? `?job_id=${jobId}` : ''}`),

  getImprovementAdvices: (body: { review_id?: number; job_id?: number }) =>
    request<any>('/interview/improvement', { method: 'POST', body: JSON.stringify(body) }),

  // Resume Optimization
  getResumeAdvise: (jobId: number) =>
    request<any>('/resume/advise', { method: 'POST', body: JSON.stringify({ job_id: jobId }) }),

  generateResume: (jobId: number) =>
    request<any>('/resume/generate', { method: 'POST', body: JSON.stringify({ job_id: jobId }) }),

  getResumeVersions: () => request<{ versions: any[] }>('/resume/versions'),

  // Sources
  getJobSources: () => request<{ sources: any[]; all_platforms: string[] }>('/jobs/sources'),

  addCustomSource: (body: {
    title: string;
    company: string;
    source_name: string;
    source_url?: string;
    city?: string;
    salary_range?: string;
    recruitment_type?: string;
    industry?: string;
    jd_text?: string;
    skills?: string[];
  }) => request<any>('/custom-source', { method: 'POST', body: JSON.stringify(body) }),

  // Health & Seed
  health: () => request<{ status: string }>('/health'),
  seed: () => request<any>('/seed', { method: 'POST' }),
};
