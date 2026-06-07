/* ================================================
   MediFinder — Main JavaScript v2.0
================================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Progress bar ─────────────────────────── */
  const bar = document.createElement('div');
  bar.className = 'progress-bar';
  document.body.prepend(bar);

  window.addEventListener('beforeunload', () => {
    bar.style.width = '70%';
  });

  /* ── Navbar scroll effect ─────────────────── */
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.classList.toggle('scrolled', window.scrollY > 10);
    }, { passive: true });
  }

  /* ── Mobile nav toggle ────────────────────── */
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (navToggle && navLinks) {
    navToggle.addEventListener('click', () => {
      navToggle.classList.toggle('open');
      navLinks.classList.toggle('open');
    });
    // close on outside click
    document.addEventListener('click', (e) => {
      if (!navbar.contains(e.target)) {
        navToggle.classList.remove('open');
        navLinks.classList.remove('open');
      }
    });
  }

  /* ── Search input smooth scroll ───────────── */
  const searchInput = document.querySelector('.search-box input');
  if (searchInput) {
    searchInput.addEventListener('focus', () =>
      searchInput.scrollIntoView({ behavior: 'smooth', block: 'center' })
    );
  }

  /* ── Password toggle ──────────────────────── */
  document.querySelectorAll('.toggle-password').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = btn.closest('.input-group').querySelector('input');
      const isHidden = input.type === 'password';
      input.type = isHidden ? 'text' : 'password';
      btn.textContent = isHidden ? '🙈' : '👁️';
    });
  });

  /* ── Auto-dismiss flash messages ──────────── */
  document.querySelectorAll('.flash').forEach((flash, i) => {
    setTimeout(() => {
      flash.style.transition = 'opacity .5s ease, transform .5s ease';
      flash.style.opacity = '0';
      flash.style.transform = 'translateY(-8px)';
      setTimeout(() => flash.remove(), 500);
    }, 4000 + i * 600);
  });

  /* ── Accordion ────────────────────────────── */
  document.querySelectorAll('.accordion-header').forEach(header => {
    header.addEventListener('click', () => {
      const item = header.closest('.accordion-item');
      const body = item.querySelector('.accordion-body');
      const isOpen = item.classList.contains('open');

      // close siblings
      document.querySelectorAll('.accordion-item.open').forEach(other => {
        if (other !== item) {
          other.classList.remove('open');
          other.querySelector('.accordion-body').classList.remove('open');
        }
      });

      item.classList.toggle('open', !isOpen);
      body.classList.toggle('open', !isOpen);
    });
  });

  /* ── Copy-to-clipboard for cred values ────── */
  document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const val = btn.dataset.copy;
      if (!val) return;
      navigator.clipboard.writeText(val).then(() => {
        const orig = btn.textContent;
        btn.textContent = '✓';
        btn.style.color = '#6ee7b7';
        setTimeout(() => {
          btn.textContent = orig;
          btn.style.color = '';
        }, 1500);
      });
    });
  });

  /* ── Animated counters ────────────────────── */
  function animateCounter(el) {
    const target = parseInt(el.textContent, 10);
    if (isNaN(target)) return;
    let current = 0;
    const step = Math.max(1, Math.ceil(target / 40));
    const interval = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current;
      if (current >= target) clearInterval(interval);
    }, 30);
  }

  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('.stat-value').forEach(el => counterObserver.observe(el));

  /* ── Fade-in on scroll ────────────────────── */
  const fadeObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animationPlayState = 'running';
        fadeObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.anim-in').forEach(el => {
    el.style.animationPlayState = 'paused';
    fadeObserver.observe(el);
  });

  /* ── Particle canvas background ───────────── */
  const canvas = document.getElementById('bg-particles');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let particles = [];
    let W, H;

    function resize() {
      W = canvas.width  = window.innerWidth;
      H = canvas.height = window.innerHeight;
    }

    class Particle {
      constructor() { this.reset(); }
      reset() {
        this.x = Math.random() * W;
        this.y = Math.random() * H;
        this.r = Math.random() * 2 + 0.5;
        this.vx = (Math.random() - 0.5) * 0.4;
        this.vy = (Math.random() - 0.5) * 0.4;
        this.alpha = Math.random() * 0.5 + 0.1;
        this.color = Math.random() > 0.5
          ? `rgba(59,130,246,${this.alpha})`
          : `rgba(139,92,246,${this.alpha})`;
      }
      update() {
        this.x += this.vx;
        this.y += this.vy;
        if (this.x < 0 || this.x > W || this.y < 0 || this.y > H) this.reset();
      }
      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.fill();
      }
    }

    function init() {
      resize();
      particles = Array.from({ length: 80 }, () => new Particle());
    }

    function loop() {
      ctx.clearRect(0, 0, W, H);

      // draw connecting lines
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(59,130,246,${0.08 * (1 - dist / 120)})`;
            ctx.lineWidth = 0.5;
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }

      particles.forEach(p => { p.update(); p.draw(); });
      requestAnimationFrame(loop);
    }

    init();
    loop();
    window.addEventListener('resize', init, { passive: true });
  }

  /* ── Result cards stagger animation ───────── */
  document.querySelectorAll('.result-card').forEach((card, i) => {
    card.style.animationDelay = `${i * 0.07}s`;
  });

  /* ── Table row confirm on delete ─────────── */
  document.querySelectorAll('.delete-link').forEach(link => {
    link.addEventListener('click', (e) => {
      if (!confirm('Are you sure you want to delete this medicine record?')) {
        e.preventDefault();
      }
    });
  });

  /* ── Input label float effect ────────────── */
  document.querySelectorAll('input, select').forEach(input => {
    input.addEventListener('focus', () => {
      input.parentElement.classList.add('focused');
    });
    input.addEventListener('blur', () => {
      input.parentElement.classList.remove('focused');
    });
  });

});
