import { getUserKey } from '../utils/userKey';

const BASE = '/api';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const isFormData = options?.body instanceof FormData;
  const headers: Record<string, string> = {
    'X-User-Key': getUserKey(),
  };
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }
  const res = await fetch(`${BASE}${url}`, {
    ...options,
    headers: { ...headers, ...(options?.headers as Record<string, string>) },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    // 尝试解析 JSON 错误体，提取友好的错误消息
    let message = `HTTP ${res.status}: ${text || res.statusText}`;
    try {
      const json = JSON.parse(text);
      if (json.error) message = json.error;
      if (json.need_manual_input) message = 'NEED_MANUAL_INPUT';
    } catch {}
    throw new Error(message);
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
    return request<any>('/resume/upload', { method: 'POST', body: fd });
  },

  // 更新不可接受项
  updateDealBreakers: (breakers: string[]) =>
    request<{ success: boolean; message: string }>('/resume/deal-breakers', { method: 'PUT', body: JSON.stringify({ deal_breakers: breakers }) }),

  // 更新兴趣画像（支持部分字段更新）
  updateInterestProfile: (fields: { preferred_industries?: string[]; preferred_roles?: string[]; preferred_cities?: string[]; salary_min?: number }) =>
    request<{ success: boolean; message: string; profile?: any }>('/resume/interest-profile', { method: 'PUT', body: JSON.stringify(fields) }),

  // 更新能力画像（支持全部字段更新）
  updateAbilityProfile: (fields: { skills?: string[]; education?: string; major?: string; experience?: string; projects?: string[] }) =>
    request<{ success: boolean; message: string; profile?: any }>('/resume/ability-profile', { method: 'PUT', body: JSON.stringify(fields) }),

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
    source_channel?: string;
    city?: string;
    salary_range?: string;
    recruitment_type?: string;
    industry?: string;
    jd_text?: string;
    skills?: string[];
  }) => request<any>('/custom-source', { method: 'POST', body: JSON.stringify(body) }),

  // 编辑/删除岗位
  updateJob: (id: number, body: {
    title?: string;
    company?: string;
    source_name?: string;
    source_url?: string;
    source_channel?: string;
    city?: string;
    salary_range?: string;
    recruitment_type?: string;
    industry?: string;
    jd_text?: string;
    skills?: string[];
  }) => request<any>(`/jobs/${id}`, { method: 'PUT', body: JSON.stringify(body) }),

  deleteJob: (id: number) =>
    request<any>(`/jobs/${id}`, { method: 'DELETE' }),

  // URL Import - 手动填写 + AI辅助导入岗位
  importJobFromURL: (body: {
    url: string;
    title: string;
    company: string;
    source_channel?: string;
    source_name?: string;
    city?: string;
    salary_range?: string;
    recruitment_type?: string;
    industry?: string;
    jd_text?: string;
    skills?: string[];
  }) =>
    request<{
      success: boolean; job_id?: number; message: string;
      duplicate?: boolean; source_platform?: string; extracted_skills?: string[];
      need_manual_input?: boolean;
    }>(
      '/jobs/import-from-url', { method: 'POST', body: JSON.stringify(body) }
    ),

  // JD Text AI 解析 - 从粘贴的JD文本智能提取岗位信息
  parseJDFromText: (jdText: string) =>
    request<{
      success: boolean;
      data?: {
        job_title: string;
        company: string;
        salary_range: string;
        city: string;
        jd_summary: string;
        skills: string[];
        industry: string;
        recruitment_type: string;
      };
      error?: string;
    }>(
      '/jobs/parse-jd-text',
      { method: 'POST', body: JSON.stringify({ jd_text: jdText }) }
    ),

  // Batch Import - 批量确认导入列表页岗位
  importJobBatch: (jobs: any[]) =>
    request<{
      success: boolean; imported: number; duplicates: number;
      failed: number; job_ids: number[]; message: string;
    }>(
      '/jobs/import-batch', { method: 'POST', body: JSON.stringify({ jobs }) }
    ),

  // Dashboard
  getDashboard: () =>
    request<{
      total_jobs: number; today_new: number;
      match_distribution: Record<string, number>;
      high_match_count: number; mid_match_count: number;
      sources: { platform: string; count: number; label: string }[];
      industries: { industry: string; cnt: number }[];
      applications: { total: number; by_status: Record<string, number> };
    }>('/dashboard'),

  // Daily Report
  getDailyReport: () =>
    request<{
      date: string; today_new_jobs: number;
      score_distribution: any[];
      weekly_applications: any[];
      top_skill_gaps: { skill: string; demand_count: number }[];
      recommended_actions: string[];
      total_matched: number;
    }>('/daily-report'),

  // User Feedback
  submitUserFeedback: (body: { type: string; title: string; description: string; contact?: string }) =>
    request<{ success: boolean; message: string }>('/user-feedback', { method: 'POST', body: JSON.stringify(body) }),

  // Health & Seed
  health: () => request<{ status: string }>('/health'),
  seed: () => request<any>('/seed', { method: 'POST' }),

  // ── 质量过滤 ──────────────────────────────────────────
  rescoreAllJobs: () =>
    request<{ success: boolean; total_jobs: number; rescored: number; cleaned: number; message: string }>(
      '/jobs/rescore-all', { method: 'POST' }
    ),

  getQualityStats: () =>
    request<{ success: boolean; stats: { total: number; high_quality: number; medium_quality: number; low_quality: number; unscored: number } }>(
      '/jobs/quality-stats'
    ),
};
