<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelBadge from '@/components/pixel/PixelBadge.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'

const router = useRouter()
const authStore = useAuthStore()

function handleAction(): void {
	if (authStore.isAuthenticated) {
		if (authStore.userRole === 'admin') router.push('/admin')
		else if (authStore.userRole === 'mentor') router.push('/mentor')
		else router.push('/student')
	} else {
		router.push('/login')
	}
}

function goToGithub(): void {
	window.location.href = 'https://github.com/Tharun-Kumar-A-01/zero1'
}
</script>

<template>
	<div class="landing-page">
		<!-- TOP NAVIGATION BAR -->
		<header class="landing-nav">
			<div class="nav-container">
				<div class="nav-brand" @click="handleAction">
					<PixelSprite name="sword" :size="24" />
					<span class="brand-title">ZERO1</span>
				</div>

				<div class="nav-actions">
					<PixelButton variant="primary" class="nav-btn" @click="handleAction">
						<PixelIcon name="login" :size="12" class="btn-icon" />
						{{ authStore.isAuthenticated ? 'Dashboard' : 'Sign In' }}
					</PixelButton>
				</div>
			</div>
		</header>

		<!-- HERO SECTION -->
		<section class="hero-section">
			<div class="hero-container">
				<h1 class="hero-title">
					Self-Hostable Daily Coding Practice for Your College & Class
				</h1>

				<p class="hero-desc">
					Deploy Zero1 directly on campus servers or private clouds. Empower engineering
					cohorts with daily aptitude and coding quests, Judge0 automated execution,
					faculty rotation scheduling, and gamified streak leaderboards.
				</p>

				<div class="hero-buttons">
					<PixelButton color="primary" size="large" @click="handleAction">
						{{ authStore.isAuthenticated ? 'Enter Arena' : 'Sign In' }}
					</PixelButton>

					<PixelButton color="secondary" size="large" @click="goToGithub">
						View Source
					</PixelButton>
				</div>
			</div>
		</section>

		<!-- 3 CORE PILLARS -->
		<section class="pillars-section">
			<div class="section-container">
				<h2 class="section-heading">Built Specifically for Colleges & Classrooms</h2>
				<p class="section-subheading">
					A self-contained platform designed to build lifelong daily coding habits and
					interview aptitude.
				</p>

				<div class="pillars-grid">
					<!-- Pillar 1 -->
					<div class="pillar-card">
						<PixelSprite name="sword" :size="32" />
						<h3 class="pillar-title">Daily Quests</h3>
						<p class="pillar-text">
							Every morning unlocks one aptitude MCQ and one hands-on coding problem
							tailored for college batches. Solving either quest maintains the
							student's daily streak.
						</p>
					</div>

					<!-- Pillar 2 -->
					<div class="pillar-card">
						<PixelSprite name="shield" :size="32" />
						<h3 class="pillar-title">Self-Hosted</h3>
						<p class="pillar-text">
							Run entirely on your department hardware or private infrastructure. Full
							data ownership of student grades, batch rosters, and source code
							submissions.
						</p>
					</div>

					<!-- Pillar 3 -->
					<div class="pillar-card">
						<PixelSprite name="trophy" :size="32" />
						<h3 class="pillar-title">Gamification</h3>
						<p class="pillar-text">
							Motivate students with persistent streak counters, milestone badges
							(Bronze, Silver, Gold, Emerald, Ruby, Diamond), and batch-filtered
							Olympic leaderboards.
						</p>
					</div>
				</div>
			</div>
		</section>

		<!-- CAMPUS FEATURES GRID -->
		<section class="features-section">
			<div class="section-container">
				<h2 class="section-heading">Institutional Features for Faculty & Admins</h2>
				<p class="section-subheading">
					Equipped with enterprise tools for smooth academic administration.
				</p>

				<div class="features-grid">
					<div class="feature-item">
						<div class="feature-head">
							<PixelSprite name="scroll" :scale="1.2" />
							<h4 class="feature-title">Faculty Rotation Scheduling</h4>
						</div>
						<p class="feature-desc">
							Assign weekly mentoring rotations among professors. Faculty draft
							curriculum-aligned problem sets with AI test-case synthesis before
							publishing.
						</p>
					</div>

					<div class="feature-item">
						<div class="feature-head">
							<PixelSprite name="chest" :scale="1.2" />
							<h4 class="feature-title">Excel & CSV Roster Onboarding</h4>
						</div>
						<p class="feature-desc">
							Upload class spreadsheets with roll numbers, department sections, and
							batch years. Intelligent mapping parses headers and registers students
							seamlessly.
						</p>
					</div>

					<div class="feature-item">
						<div class="feature-head">
							<PixelSprite name="thunder" :scale="1.2" />
							<h4 class="feature-title">Automated Judge0 Sandbox</h4>
						</div>
						<p class="feature-desc">
							Execute code safely across Python, C++, Java, and JavaScript against
							sample and hidden edge test cases with memory and execution timeout
							constraints.
						</p>
					</div>

					<div class="feature-item">
						<div class="feature-head">
							<PixelSprite name="gem_emerald" :scale="1.2" />
							<h4 class="feature-title">Customizable Badges & Milestones</h4>
						</div>
						<p class="feature-desc">
							Admins configure custom XP milestones, streak thresholds, and problem
							count rewards with retro gem badges to match the semester's learning
							outcomes.
						</p>
					</div>
				</div>
			</div>
		</section>

		<!-- SIMPLE 3-STEP FLOW -->
		<section class="flow-section">
			<div class="section-container">
				<div class="flow-grid">
					<div class="flow-step">
						<div class="step-number">1</div>
						<h4 class="step-title">Deploy & Import Roster</h4>
						<p class="step-desc">
							Deploy with Docker or local server and import student rosters by batch
							year and section in seconds.
						</p>
					</div>

					<div class="flow-step">
						<div class="step-number">2</div>
						<h4 class="step-title">Schedule Faculty Rotations</h4>
						<p class="step-desc">
							Mentors curate daily aptitude MCQs and coding challenges with automated
							test-case generators.
						</p>
					</div>

					<div class="flow-step">
						<div class="step-number">3</div>
						<h4 class="step-title">Students Code Every Day</h4>
						<p class="step-desc">
							Students solve quests, preserve streaks, unlock custom gem badges, and
							climb the cohort Hall of Fame.
						</p>
					</div>
				</div>
			</div>
		</section>

		<!-- CALL TO ACTION SECTION -->
		<section class="cta-section">
			<div class="section-container">
				<div class="cta-box">
					<PixelSprite name="flame" :scale="2" class="cta-icon" />
					<h2 class="cta-title">Ready to Level Up Your Class?</h2>
					<p class="cta-desc">
						Build discipline, consistency, and campus-wide coding culture. Sign in with
						your department credentials to start today's quest.
					</p>
					<PixelButton variant="primary" size="large" @click="handleAction">
						{{ authStore.isAuthenticated ? 'Resume Daily Quests' : 'Sign In' }}
					</PixelButton>
				</div>
			</div>
		</section>

		<!-- FOOTER -->
		<footer class="landing-footer">
			<div class="footer-container">
				<div class="footer-brand">
					<PixelSprite name="sword" :size="18" />
					<span>ZERO1 • SELF-HOSTED CAMPUS CODING GUILD</span>
				</div>
			</div>
		</footer>
	</div>
</template>

<style scoped>
.landing-page {
	min-height: 100vh;
	background-color: var(--pixel-bg, #121218);
	color: var(--pixel-text, #f0f0f5);
	font-family: var(--font-body, system-ui, sans-serif);
	display: flex;
	flex-direction: column;
}

/* TOP NAVIGATION */
.landing-nav {
	position: sticky;
	top: 0;
	z-index: 100;
	background-color: var(--pixel-surface, #1e1e24);
	border-bottom: 2px solid var(--pixel-border, #3a3a4c);
}

.nav-container {
	max-width: 1100px;
	margin: 0 auto;
	padding: 0.85rem 1.5rem;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.nav-brand {
	display: flex;
	align-items: center;
	gap: 10px;
	cursor: pointer;
}

.brand-title {
	font-family: var(--pixel-font, monospace);
	font-size: 1.4rem;
	font-weight: 700;
	letter-spacing: 0.05em;
	color: var(--pixel-text, #f0f0f5);
}

.brand-tag {
	font-family: var(--pixel-font, monospace);
	font-size: 0.7rem;
	padding: 2px 6px;
	background: rgba(99, 102, 241, 0.2);
	border: 1px solid var(--pixel-primary, #6366f1);
	color: var(--pixel-primary, #6366f1);
	letter-spacing: 0.05em;
}

.nav-actions {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.btn-sprite {
	margin-right: 0.4rem;
	vertical-align: middle;
}

.btn-icon {
	margin-right: 0.4rem;
	vertical-align: middle;
}

.badge-sprite {
	margin-right: 0.35rem;
	vertical-align: middle;
}

/* HERO SECTION */
.hero-section {
	padding: 5rem 1.5rem 4.5rem;
	background: linear-gradient(
		180deg,
		var(--pixel-surface, #1e1e24) 0%,
		var(--pixel-bg, #121218) 100%
	);
	border-bottom: 2px solid var(--pixel-border, #3a3a4c);
	text-align: center;
}

.hero-container {
	max-width: 820px;
	margin: 0 auto;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 1.5rem;
}

.hero-badge-wrap {
	display: flex;
	justify-content: center;
}

.hero-title {
	font-family: var(--pixel-font, monospace);
	font-size: 2.35rem;
	line-height: 1.25;
	color: var(--pixel-text, #f0f0f5);
	margin: 0;
	letter-spacing: 0.5px;
}

.hero-desc {
	font-size: 1.1rem;
	line-height: 1.6;
	color: var(--pixel-text-muted, #9ca3af);
	margin: 0;
	max-width: 680px;
}

.hero-buttons {
	display: flex;
	gap: 1rem;
	margin-top: 0.5rem;
	justify-content: center;
	flex-wrap: wrap;
}

/* 3 CORE PILLARS */
.pillars-section {
	padding: 4.5rem 1.5rem;
	border-bottom: 2px solid var(--pixel-border, #3a3a4c);
}

.section-container {
	max-width: 1000px;
	margin: 0 auto;
}

.section-heading {
	font-family: var(--pixel-font, monospace);
	font-size: 1.75rem;
	text-align: center;
	margin: 0 0 0.5rem;
	color: var(--pixel-text, #f0f0f5);
}

.section-subheading {
	text-align: center;
	font-size: 0.95rem;
	color: var(--pixel-text-muted, #9ca3af);
	margin: 0 0 3rem;
}

.pillars-grid {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 1.5rem;
}

.pillar-card {
	background-color: var(--pixel-surface, #1e1e24);
	border: 2px solid var(--pixel-border, #3a3a4c);
	padding: 2rem 1.5rem;
	display: flex;
	flex-direction: column;
	gap: 0.85rem;
	align-items: flex-start;
	box-shadow: 0 4px 0 rgba(0, 0, 0, 0.4);
}

.pillar-icon {
	width: 50px;
	height: 50px;
	background-color: rgba(0, 0, 0, 0.3);
	border: 2px solid var(--pixel-border, #3a3a4c);
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 0.25rem;
}

.pillar-title {
	font-family: var(--pixel-font, monospace);
	font-size: 1.15rem;
	margin: 0;
	color: var(--pixel-text, #f0f0f5);
}

.pillar-text {
	font-size: 0.9rem;
	line-height: 1.55;
	color: var(--pixel-text-muted, #9ca3af);
	margin: 0;
}

/* CAMPUS FEATURES SECTION */
.features-section {
	padding: 4rem 1.5rem;
	border-bottom: 2px solid var(--pixel-border, #3a3a4c);
	background-color: var(--pixel-surface, #1e1e24);
}

.features-grid {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 1.5rem;
}

.feature-item {
	background: var(--pixel-bg, #121218);
	border: 2px solid var(--pixel-border, #3a3a4c);
	padding: 1.5rem;
	display: flex;
	flex-direction: column;
	gap: 0.75rem;
}

.feature-head {
	display: flex;
	align-items: center;
	gap: 0.75rem;
}

.feature-title {
	font-family: var(--pixel-font, monospace);
	font-size: 1.05rem;
	margin: 0;
	color: var(--pixel-text, #f0f0f5);
}

.feature-desc {
	font-size: 0.88rem;
	line-height: 1.5;
	color: var(--pixel-text-muted, #9ca3af);
	margin: 0;
}

/* FLOW SECTION */
.flow-section {
	padding: 3.5rem 1.5rem;
	background-color: var(--pixel-bg, #121218);
	border-bottom: 2px solid var(--pixel-border, #3a3a4c);
}

.flow-grid {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 2rem;
}

.flow-step {
	display: flex;
	flex-direction: column;
	gap: 0.6rem;
}

.step-number {
	font-family: var(--pixel-font, monospace);
	font-size: 1.25rem;
	color: var(--pixel-primary, #6366f1);
	width: 36px;
	height: 36px;
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: var(--pixel-surface, #1e1e24);
	border: 2px solid var(--pixel-border, #3a3a4c);
}

.step-title {
	font-family: var(--pixel-font, monospace);
	font-size: 1.05rem;
	margin: 0;
	color: var(--pixel-text, #f0f0f5);
}

.step-desc {
	font-size: 0.88rem;
	color: var(--pixel-text-muted, #9ca3af);
	margin: 0;
	line-height: 1.45;
}

/* CTA BOX */
.cta-section {
	padding: 4.5rem 1.5rem;
}

.cta-box {
	background-color: var(--pixel-surface, #1e1e24);
	border: 2px solid var(--pixel-border, #3a3a4c);
	box-shadow: 0 6px 0 rgba(0, 0, 0, 0.4);
	padding: 3rem 2rem;
	text-align: center;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 1.25rem;
	max-width: 680px;
	margin: 0 auto;
}

.cta-icon {
	margin-bottom: 0.25rem;
}

.cta-title {
	font-family: var(--pixel-font, monospace);
	font-size: 1.65rem;
	margin: 0;
	color: var(--pixel-text, #f0f0f5);
}

.cta-desc {
	font-size: 0.95rem;
	color: var(--pixel-text-muted, #9ca3af);
	margin: 0;
	max-width: 500px;
}

/* FOOTER */
.landing-footer {
	margin-top: auto;
	border-top: 2px solid var(--pixel-border, #3a3a4c);
	background-color: var(--pixel-surface, #1e1e24);
	padding: 1.75rem 1.5rem;
}

.footer-container {
	max-width: 1000px;
	margin: 0 auto;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0.5rem;
	text-align: center;
}

.footer-brand {
	display: flex;
	align-items: center;
	gap: 8px;
	font-family: var(--pixel-font, monospace);
	font-size: 0.85rem;
	color: var(--pixel-text-muted, #9ca3af);
}

.footer-copy {
	font-size: 0.8rem;
	color: var(--pixel-text-muted, #9ca3af);
	margin: 0;
}

/* RESPONSIVE */
@media (max-width: 820px) {
	.hero-title {
		font-size: 1.85rem;
	}

	.pillars-grid,
	.features-grid,
	.flow-grid {
		grid-template-columns: 1fr;
		gap: 1.25rem;
	}
}
</style>
