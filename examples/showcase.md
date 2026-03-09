---
title: "Gradient Descent Demystified"
subtitle: "From Intuition to Implementation"
author: "Your Name — Your University"
date: "March 2026"
theme: "metropolis"
classoption: "aspectratio=169"
header-includes:
  - \usepackage{booktabs}
  - \usepackage{amsmath,amssymb}
  - \setbeamertemplate{navigation symbols}{}
  - \setbeamerfont{normal text}{size=\small}
  - \AtBeginDocument{\usebeamerfont{normal text}}
---

## The Core Idea

**Problem:** Find $\theta^*$ that minimizes a loss function $\mathcal{L}(\theta)$

**Solution:** Take steps proportional to the negative gradient:

$$\theta_{t+1} = \theta_t - \eta \nabla \mathcal{L}(\theta_t)$$

- $\eta$ is the **learning rate** — too large and you overshoot, too small and you crawl
- The gradient $\nabla \mathcal{L}$ points uphill; we go the opposite way

---

## Why It Works

**Taylor expansion** around current point $\theta_t$:

$$\mathcal{L}(\theta_t + \delta) \approx \mathcal{L}(\theta_t) + \nabla \mathcal{L}(\theta_t)^\top \delta + \frac{1}{2} \delta^\top H \delta$$

Choosing $\delta = -\eta \nabla \mathcal{L}$:

$$\mathcal{L}(\theta_{t+1}) \approx \mathcal{L}(\theta_t) - \eta \|\nabla \mathcal{L}\|^2 + O(\eta^2)$$

For small enough $\eta$, the loss **always decreases**.

---

## Variants at a Glance

\renewcommand{\arraystretch}{1.3}

| Method | Update Rule | Key Property |
|--------|-----------|-------------|
| **SGD** | $\theta - \eta g_t$ | Stochastic, noisy |
| **Momentum** | $\theta - \eta v_t$, $v_t = \beta v_{t-1} + g_t$ | Accelerates in consistent directions |
| **Adam** | Adaptive $\eta$ per parameter | Combines momentum + RMSprop |
| **AdaGrad** | $\eta / \sqrt{\sum g^2}$ | Good for sparse gradients |

All reduce to the same principle: **follow the gradient, but be smart about step size**.

---

## Convergence Guarantees

For $L$-smooth, $\mu$-strongly convex functions:

$$\mathcal{L}(\theta_T) - \mathcal{L}(\theta^*) \leq \left(1 - \frac{\mu}{L}\right)^T \left[\mathcal{L}(\theta_0) - \mathcal{L}(\theta^*)\right]$$

**Key quantities:**

- **Condition number** $\kappa = L/\mu$ — ratio of curvatures
- **Convergence rate** — linear: $O\!\left(\kappa \log \frac{1}{\varepsilon}\right)$ iterations
- **Acceleration** (Nesterov): $O\!\left(\sqrt{\kappa} \log \frac{1}{\varepsilon}\right)$ — provably optimal

---

## Summary

1. Gradient descent minimizes by following $-\nabla \mathcal{L}$
2. Taylor expansion guarantees descent for small $\eta$
3. Modern variants (Adam, momentum) adapt the step size
4. Convergence rate depends on the **condition number** $\kappa = L/\mu$
5. Nesterov acceleration achieves the optimal $O(\sqrt{\kappa})$ rate

\vspace{1em}

**Further reading:**

- Bottou et al. (2018) — *Optimization Methods for Large-Scale ML*
- Ruder (2016) — *An Overview of Gradient Descent Optimization*
