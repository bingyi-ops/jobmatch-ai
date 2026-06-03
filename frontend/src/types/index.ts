export type Platform = 'official' | 'boss_zhipin' | 'xiaohongshu' | 'wechat_public' | 'liepin' | 'lagou' | 'zhilian' | '51job' | 'shixiseng' | 'zhihu' | 'referral' | 'school_career' | 'bilibili' | 'douyin' | 'weibo' | 'custom';
export type RecruitType = 'daily_intern' | 'summer_intern' | 'autumn_recruit' | 'spring_recruit' | 'experienced';
export type ApplicationStatus = 'applied' | 'interviewing' | 'offer' | 'rejected';
export type IgnoreReason = 'salary_too_low' | 'location_mismatch' | 'skill_mismatch' | 'not_interested';

export interface Job {
  id: number;
  title: string;
  company: string;
  jd_text: string;
  jd_skills: string[];
  jd_profile: JdProfile | null;
  city: string;
  salary_range: string;
  recruitment_type: RecruitType;
  industry: string;
  source_platform: Platform;
  source_url: string;
  custom_source_name?: string;
  custom_source_url?: string;
  application_deadline: string;
  posted_at: string;
}

export interface JdProfile {
  knowledge: string[];
  skills: string[];
  abilities: string[];
  values: string[];
}

export interface MatchRecord {
  id: number;
  job_id: number;
  interest_score: number;
  ability_score: number;
  market_score: number;
  overlap_score: number;
  match_reasons: string;
  created_at: string;
  feedback?: { action: string; ignore_reason?: string } | null;
}

export interface JobCard extends Job, MatchRecord {
  feedback?: { action: string; ignore_reason?: string } | null;
}

export interface Application {
  id: number;
  job_id: number;
  match_record_id: number | null;
  status: ApplicationStatus;
  notes: {
    interview_time?: string;
    hr_contact?: string;
    interview_notes?: string;
    interview_history?: any[];
    other?: string;
    last_interview_review_id?: number;
    last_interview_score?: number;
    last_resume_version_id?: number;
    resume_optimized?: boolean;
  } | null;
  applied_at: string;
  updated_at: string;
  job_title: string;
  job_company: string;
  job_source_url: string;
}

export interface ApplicationStats {
  total: number;
  by_status: Record<string, number>;
  score_distribution: { range: string; cnt: number }[];
  weekly_trend: { week: string; applied: number; offer: number }[];
}

export interface ResumeProfile {
  has_resume: boolean;
  interest_profile?: {
    preferred_industries: string[];
    preferred_roles: string[];
    work_style: string[];
  };
  ability_profile?: {
    skills: string[];
    education: string;
    experience: string;
    projects: string[];
  };
  deal_breakers?: string[];
}

export interface CompanyInfo {
  company: string;
  funding_stage: string;
  employee_scale: string;
  industry_position: string;
  recent_news: string;
  culture_keywords: string[];
  disclaimer: string;
}

// ── Resume Optimization ──
export interface ResumeAdvice {
  type: 'strength' | 'gap' | 'project' | 'keyword' | 'format';
  title: string;
  content: string;
  skills?: string[];
}

export interface ResumeAdviseResult {
  job_title: string;
  job_company: string;
  matched_skills: string[];
  missing_skills: string[];
  match_rate: number;
  advices: ResumeAdvice[];
}

export interface GeneratedResume {
  personal_info: { name: string; phone: string; email: string; city: string };
  summary: string;
  core_skills: string[];
  target_job: string;
  target_company: string;
  related_projects: { name: string; description: string; skills_used: string[]; result: string }[];
  jd_matched_points: string[];
  optimization_notes: string[];
}

export interface ResumeVersion {
  id: number;
  resume_id: number;
  version: number;
  content_json: string;
  title: string;
  target_job_title: string;
  improvement_notes: string;
  created_at: string;
}

// ── Interview Review ──
export interface InterviewReview {
  id: number;
  application_id: number;
  job_id: number;
  review_text: string;
  score_self: number;
  questions_asked: string;
  difficult_questions: string;
  ai_analysis: string;
  improvement_advices: string;
  strengths: string;
  weaknesses: string;
  created_at: string;
}

export interface AIAnalysis {
  overall_score: number;
  score_breakdown: {
    technical: number;
    communication: number;
    problem_solving: number;
    culture_fit: number;
  };
  strengths: string[];
  weaknesses: string[];
  key_takeaways: string;
}

export interface ImprovementAdvice {
  category: string;
  priority: string;
  action: string;
  timeline: string;
  resources: string;
}

export interface ImprovementResult {
  review_id: number;
  review_score: number;
  ai_score: number;
  strengths: string[];
  weaknesses: string[];
  improvement_advices: ImprovementAdvice[];
  next_steps: {
    before_next_interview: { step: number; action: string; detail: string; duration: string }[];
    long_term_growth: string[];
    resume_update_suggestions: string[];
    priority_advices: ImprovementAdvice[];
  };
  job_title: string;
  job_company: string;
}

// ── Source Platforms ──
export interface SourcePlatform {
  platform: string;
  count: number;
  label: string;
}

export const PLATFORM_LABELS: Record<string, string> = {
  official: '企业官网',
  boss_zhipin: 'Boss直聘',
  xiaohongshu: '小红书',
  wechat_public: '微信公众号',
  liepin: '猎聘',
  lagou: '拉勾',
  zhilian: '智联招聘',
  '51job': '前程无忧',
  shixiseng: '实习僧',
  zhihu: '知乎',
  referral: '内推/师兄师姐推荐',
  school_career: '学校就业网',
  bilibili: 'B站',
  douyin: '抖音',
  weibo: '微博',
  custom: '自定义来源',
};
