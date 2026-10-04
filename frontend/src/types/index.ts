export interface UserProfile {
	id: number
	name: string
	email: string
	role: 'admin' | 'mentor' | 'student'
	roll_number?: string | null
	year_batch?: string | null
	department?: string | null
	section?: string | null
	current_streak?: number
	longest_streak?: number
	total_points?: number
}

export interface SampleTestCase {
	id: number
	input_data: string
	expected_output: string
	is_sample: boolean
}

export interface CodingQuestionData {
	id: number
	title: string
	word_problem_text: string
	constraints_text: string
	difficulty: 'easy' | 'medium' | 'hard'
	allowed_languages: string[]
	time_limit_ms: number
	memory_limit_kb: number
	function_name?: string
	parameter_definitions?: Array<{ name: string; type: string }>
	return_type?: string
	starter_templates?: Record<string, string>
	sample_test_cases: SampleTestCase[]
}

export interface MCQQuestionData {
	id: number
	prompt_text: string
	options: string[]
	difficulty: 'easy' | 'medium' | 'hard'
	tags: string[]
}

export interface DailyChallengeData {
	id: number
	student_id: number
	assignment_date: string
	mcq_status: 'pending' | 'correct' | 'incorrect'
	coding_status: 'pending' | 'attempted_unsolved' | 'solved'
	coding_started_at?: string | null
	coding_completed_at?: string | null
	coding_time_spent_seconds?: number | null
	elapsed_seconds?: number | null
	submission_attempts_count?: number
	mcq_question: MCQQuestionData | null
	coding_question: CodingQuestionData | null
}

export interface CodeSubmissionResult {
	execution_status: string
	mode?: 'run' | 'submit'
	phase?: 'sample' | 'hidden' | 'review'
	test_cases_passed: number
	test_cases_total: number
	runtime_ms?: number | null
	memory_kb?: number | null
	compiler_output?: string | null
	error_message?: string | null
	points_awarded?: number
	current_streak?: number
	is_day_solved?: boolean
	ai_flagged?: boolean
	ai_review_notes?: string | null
	coding_time_spent_seconds?: number | null
	submission_attempts_count?: number
}

export interface StudentRewardBadge {
	id: number
	reward_name: string
	reward_type: string
	awarded_at: string
}

export interface ProgressData {
	current_streak: number
	longest_streak: number
	last_active_date?: string | null
	total_points: number
	badges: StudentRewardBadge[]
}

export interface LeaderboardEntry {
	rank: number
	student_id: number
	name: string
	roll_number: string
	year_batch: string
	department?: string | null
	total_points: number
	current_streak: number
}

export interface MCQItem {
	id: number
	prompt_text: string
	options: string[]
	correct_option_index: number
	explanation?: string | null
	difficulty: string
	tags: string[]
}

export interface TestCaseItem {
	id?: number
	input_data: string
	expected_output: string
	is_sample: boolean
	is_stress_case: boolean
	source: string
}

export interface CodingQuestionItem {
	id: number
	title: string
	word_problem_text: string
	constraints_text: string
	difficulty: string
	time_limit_ms: number
	memory_limit_kb: number
	function_name?: string
	parameter_definitions?: Array<{ name: string; type: string }>
	return_type?: string
	starter_templates?: Record<string, string>
	sample_test_cases?: TestCaseItem[]
	hidden_test_cases?: TestCaseItem[]
	all_test_cases?: TestCaseItem[]
}

export interface QuestionSetData {
	id: number
	mentor_assignment_id: number
	week_start_date: string
	status: 'draft' | 'published' | 'archived'
	mcqs: MCQItem[]
	coding_questions: CodingQuestionItem[]
}

export interface FlaggedSubmission {
	id: number
	daily_assignment_id: number
	language: string
	source_code?: string
	execution_status: string
	ai_review_status: string
	ai_review_notes?: string | null
	submitted_at?: string
	created_at?: string
}

export interface UserItem {
	id: number
	name: string
	email: string
	role: 'admin' | 'mentor' | 'student'
	roll_number?: string | null
	year_batch?: string | null
	department?: string | null
	section?: string | null
	is_active: boolean
}

export interface RotationItem {
	id: number
	user_id: number
	week_start_date: string
	week_end_date: string
	status: 'upcoming' | 'active' | 'completed' | 'cancelled'
}

export interface ImportJobResponse {
	job_id: number
	sample_grid: string[][]
	inferred_mapping: {
		header_row_index: number
		data_row_start_index: number
		column_mapping: Record<string, number>
		confidence: number
	}
}

export interface CustomLeaveItem {
	id: number
	title: string
	start_date: string
	end_date: string
	description?: string | null
	created_by_admin_id: number
}

