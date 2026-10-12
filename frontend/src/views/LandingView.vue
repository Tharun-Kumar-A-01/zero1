<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import PixelButton from '@/components/pixel/PixelButton.vue'
import PixelSprite from '@/components/pixel/PixelSprite.vue'
import PixelIcon from '@/components/pixel/PixelIcon.vue'
import ThemeToggle from '@/components/common/ThemeToggle.vue'

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
					<ThemeToggle size="small" />
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
					Self-Hostable Daily Coding Practice
				</h1>

				<p class="hero-desc">
					A gamified coding platform for colleges and classrooms. Daily aptitude and
					code quests, faculty rotations, automated test execution, and persistent streaks.
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

		<!-- CORE PILLARS & FEATURES -->
		<section class="pillars-section">
			<div class="section-container">
				<h2 class="section-heading">Built for College Classrooms</h2>
				<p class="section-subheading">
					Everything you need to run daily coding practice with full data privacy.
				</p>

				<div class="pillars-grid">
					<!-- Card 1 -->
					<div class="pillar-card">
						<PixelSprite name="sword" :size="28" />
						<h3 class="pillar-title">Daily Quests</h3>
						<p class="pillar-text">
							1 aptitude MCQ and 1 coding challenge unlocked daily. Solving either quest keeps the streak alive.
						</p>
					</div>

					<!-- Card 2 -->
					<div class="pillar-card">
						<PixelSprite name="shield" :size="28" />
						<h3 class="pillar-title">Self-Hosted</h3>
						<p class="pillar-text">
							Deploy on campus servers or private clouds. Full ownership of student submissions and data.
						</p>
					</div>

					<!-- Card 3 -->
					<div class="pillar-card">
						<PixelSprite name="scroll" :size="28" />
						<h3 class="pillar-title">Faculty Rotations</h3>
						<p class="pillar-text">
							Schedule weekly mentor rotations. Faculty author questions with automated test-case synthesis.
						</p>
					</div>

					<!-- Card 4 -->
					<div class="pillar-card">
						<PixelSprite name="chest" :size="28" />
						<h3 class="pillar-title">Roster Onboarding</h3>
						<p class="pillar-text">
							Import class spreadsheets with roll numbers, sections, and batch years in seconds.
						</p>
					</div>

					<!-- Card 5 -->
					<div class="pillar-card">
						<PixelSprite name="thunder" :size="28" />
						<h3 class="pillar-title">Automated Sandbox</h3>
						<p class="pillar-text">
							Multi-language code execution in a secure Judge0 sandbox with custom edge test cases.
						</p>
					</div>

					<!-- Card 6 -->
					<div class="pillar-card">
						<PixelSprite name="trophy" :size="28" />
						<h3 class="pillar-title">Gamified Streaks</h3>
						<p class="pillar-text">
							Motivate daily consistency with XP rewards, streak multipliers, and custom milestone badges.
						</p>
					</div>
				</div>
			</div>
		</section>

		<!-- SIMPLE 3-STEP FLOW -->
		<section class="flow-section">
			<div class="section-container">
				<h2 class="section-heading">How It Works</h2>
				<p class="section-subheading">Simple setup for faculty, seamless daily practice for students.</p>
				<div class="flow-grid">
					<div class="flow-step">
						<div class="step-number">1</div>
						<h4 class="step-title">Deploy & Import</h4>
						<p class="step-desc">
							Run via Docker and upload your department student roster.
						</p>
					</div>

					<div class="flow-step">
						<div class="step-number">2</div>
						<h4 class="step-title">Rotate Mentors</h4>
						<p class="step-desc">
							Faculty curate weekly problem sets aligned with coursework.
						</p>
					</div>

					<div class="flow-step">
						<div class="step-number">3</div>
						<h4 class="step-title">Daily Practice</h4>
						<p class="step-desc">
							Students solve quests daily, maintain streaks, and level up.
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
					<h2 class="cta-title">Ready to Start Today's Quest?</h2>
					<p class="cta-desc">
						Sign in with your campus account and start coding.
					</p>
					<PixelButton variant="primary" size="large" @click="handleAction">
						{{ authStore.isAuthenticated ? 'Enter Arena' : 'Sign In' }}
					</PixelButton>
				</div>
			</div>
		</section>

		<!-- FOOTER -->
		<footer class="landing-footer">
			<div class="footer-container">
				<div class="footer-brand">
					<PixelSprite name="sword" :size="18" />
					<span>ZERO1 • SELF-HOSTED CODING PRACTICE</span>
				</div>
			</div>
		</footer>
	</div>
</template>

<style scoped>
.landing-page {
	min-height: 100vh;
	background-color: var(--pixel-bg);
	color: var(--pixel-text);
	font-family: var(--font-body, system-ui, sans-serif);
	display: flex;
	flex-direction: column;
}

/* TOP NAVIGATION */
.landing-nav {
	position: sticky;
	top: 0;
	z-index: 100;
	background-color: var(--pixel-surface);
	border-bottom: 2px solid var(--pixel-border);
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
	color: var(--pixel-text);
}

.brand-tag {
	font-family: var(--pixel-font, monospace);
	font-size: 0.7rem;
	padding: 2px 6px;
	background: var(--pixel-selection-bg);
	border: 1px solid var(--pixel-primary);
	color: var(--pixel-primary);
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
		var(--pixel-surface) 0%,
		var(--pixel-bg) 100%
	);
	border-bottom: 2px solid var(--pixel-border);
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
	color: var(--pixel-text);
	margin: 0;
	letter-spacing: 0.5px;
}

.hero-desc {
	font-size: 1.1rem;
	line-height: 1.6;
	color: var(--pixel-text-muted);
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
	border-bottom: 2px solid var(--pixel-border);
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
	color: var(--pixel-text);
}

.section-subheading {
	text-align: center;
	font-size: 0.95rem;
	color: var(--pixel-text-muted);
	margin: 0 0 3rem;
}

.pillars-grid {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 1.5rem;
}

.pillar-card {
	background-color: var(--pixel-surface);
	border: 2px solid var(--pixel-border);
	padding: 2rem 1.5rem;
	display: flex;
	flex-direction: column;
	gap: 0.85rem;
	align-items: flex-start;
	box-shadow: 0 4px 0 var(--pixel-border-dark);
}

.pillar-icon {
	width: 50px;
	height: 50px;
	background-color: var(--pixel-surface-raised);
	border: 2px solid var(--pixel-border);
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 0.25rem;
}

.pillar-title {
	font-family: var(--pixel-font, monospace);
	font-size: 1.15rem;
	margin: 0;
	color: var(--pixel-text);
}

.pillar-text {
	font-size: 0.9rem;
	line-height: 1.55;
	color: var(--pixel-text-muted);
	margin: 0;
}

/* FLOW SECTION */
.flow-section {
	padding: 3.5rem 1.5rem;
	background-color: var(--pixel-bg);
	border-bottom: 2px solid var(--pixel-border);
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
	color: var(--pixel-primary);
	width: 36px;
	height: 36px;
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: var(--pixel-surface);
	border: 2px solid var(--pixel-border);
}

.step-title {
	font-family: var(--pixel-font, monospace);
	font-size: 1.05rem;
	margin: 0;
	color: var(--pixel-text);
}

.step-desc {
	font-size: 0.88rem;
	color: var(--pixel-text-muted);
	margin: 0;
	line-height: 1.45;
}

/* CTA BOX */
.cta-section {
	padding: 4.5rem 1.5rem;
}

.cta-box {
	background-color: var(--pixel-surface);
	border: 2px solid var(--pixel-border);
	box-shadow: 0 6px 0 var(--pixel-border-dark);
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
	color: var(--pixel-text);
}

.cta-desc {
	font-size: 0.95rem;
	color: var(--pixel-text-muted);
	margin: 0;
	max-width: 500px;
}

/* FOOTER */
.landing-footer {
	margin-top: auto;
	border-top: 2px solid var(--pixel-border);
	background-color: var(--pixel-surface);
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
	color: var(--pixel-text-muted);
}

.footer-copy {
	font-size: 0.8rem;
	color: var(--pixel-text-muted);
	margin: 0;
}

/* RESPONSIVE */
@media (max-width: 820px) {
	.hero-title {
		font-size: 1.85rem;
	}

	.pillars-grid,
	.flow-grid {
		grid-template-columns: 1fr;
		gap: 1.25rem;
	}
}
</style>
