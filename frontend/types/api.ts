export interface DepartmentRead {
  id: string;
  code: string;
  name: string;
}

export interface TermRead {
  id: string;
  name: string;
  year: number;
  season: string;
  is_active_for_planning: boolean;
}

export interface CourseTopicRead {
  topic: string;
}

export interface CourseSummary {
  id: string;
  code: string;
  title: string;
  credit_hours: number;
  level: string;
  department: DepartmentRead;
  topics: CourseTopicRead[];
}

export interface CourseRead extends CourseSummary {
  description: string | null;
}

export interface ProfessorRatingRead {
  overall_rating: number;
  teaching_rating: number | null;
  difficulty_rating: number | null;
  would_take_again_pct: number | null;
  num_ratings: number;
  source_type: string;
  confidence: number;
}

export interface ProfessorSummary {
  id: string;
  name: string;
  title: string | null;
}

export interface ProfessorRead {
  id: string;
  name: string;
  title: string | null;
  email: string | null;
  department: DepartmentRead | null;
  rating: ProfessorRatingRead | null;
}

export interface GradeDistributionResponse {
  total_students: number;
  total_withdrawals: number;
  num_terms: number;
  mean_gpa: number | null;
  a_range_pct: number | null;
  b_range_pct: number | null;
  c_range_pct: number | null;
  d_or_f_range_pct: number | null;
  withdrawal_pct: number | null;
  bucket_counts: Record<string, number>;
  disclaimer: string;
}

export interface SectionMeetingRead {
  day_of_week: string;
  start_time: string;
  end_time: string;
  room_id: string | null;
}

export interface SectionRead {
  id: string;
  section_number: string;
  delivery_mode: string;
  seats_total: number;
  seats_available: number;
  course: CourseSummary;
  term: TermRead;
  professor: ProfessorSummary | null;
  meetings: SectionMeetingRead[];
}

export interface HardConstraints {
  delivery_modes: string[] | null;
  earliest_start_time: string | null;
  latest_start_time: string | null;
  exclude_days: string[] | null;
  minimum_professor_rating: number | null;
  level: string | null;
}

export interface SoftPreferences {
  prefer_delivery_modes: string[] | null;
  prefer_higher_rated_professor: boolean;
  prefer_easier_grading: boolean;
  prefer_online_exams: boolean;
  prefer_fewer_campus_days: boolean;
}

export interface ParsedRequirement {
  raw_query: string;
  topic: string | null;
  hard_constraints: HardConstraints;
  soft_preferences: SoftPreferences;
  unsupported_notes: string[];
  parser_source: string;
}

export interface ScheduleResult {
  strategy: string;
  label: string;
  sections: SectionRead[];
  total_credits: number;
  campus_days: string[];
  average_fit_score: number;
}

export interface ScheduleGenerateResponse {
  parsed: ParsedRequirement;
  schedules: Record<string, ScheduleResult | null>;
  notes: string[];
}

export interface ScheduleGenerateRequest {
  query: string;
  min_credits: number;
  max_credits: number;
}
