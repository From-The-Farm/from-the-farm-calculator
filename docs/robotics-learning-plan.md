# Robotics Engineering: A Learning Plan for a 10-Year-Old

*Researched September 2026. Prices and season dates are approximate — verify before buying or registering.*

---

## 0. The honest framing

Robotics engineering isn't one skill. It's four disciplines stacked on top of each other, plus one meta-skill that matters more than any of them:

| Pillar | What it really is | What he does at 10 |
|---|---|---|
| **Mechanical** | How things move, hold together, transmit force | Gears, levers, linkages, chassis, CAD |
| **Electronics** | Power, signals, sensors, actuators | Circuits, motors, voltage, breadboards |
| **Software** | The sense → decide → act loop | Scratch → blocks → Python |
| **Math & physics** | The language the other three run on | Ratios, coordinates, algebra, later trig |
| **→ Debugging** | *The actual job.* Robots fail constantly. | Isolate a variable. Test one thing. |

**At 10, the goal is not to "learn robotics."** The goal is:

1. **Keep the fire lit.** A kid who's still interested at 13 beats a kid who was skilled at 11 and burned out.
2. **Go broad and shallow** across all four pillars, so he finds which one he loves.
3. **Build the habit of finishing and documenting projects.**

The guiding principle: **a finished ugly robot beats an unfinished beautiful one.** Ship small things often.

The single biggest predictor of whether he's doing this at 16 isn't talent. It's whether the early experience was *his project* or *your project.*

---

## 1. Do this first: the 30-day kickstart ($0)

**Spend nothing for the first month.** This isn't frugality — it's diagnosis. You're finding out *what kind of interested* he is before you spend money. Some kids are builders who tolerate code. Some are coders who tolerate building. The kit you buy should match the kid you actually have.

Everything below is free, browser-based, and needs no hardware.

### Week 1 — Scratch (does he like making things behave?)
- Make a Scratch account at **scratch.mit.edu** (parent-created for under-13s)
- Do 3 starter tutorials, then make one original game
- Optional stretch: Harvard's free **CS50 Scratch** course at [cs50.harvard.edu/scratch](https://cs50.harvard.edu/scratch)
- **Milestone:** a game with a score and a win condition, that he designed

### Week 2 — micro:bit simulator (does he like sensors?)
- Go to **makecode.microbit.org**. It has a built-in on-screen simulator — you do *not* need the hardware
- Build: a reaction-timer game, a step counter, a digital compass
- **Milestone:** a program that reacts to a sensor input (shake, tilt, light)

### Week 3 — VEXcode VR (does he like robots specifically?)
- **vexrobotics.com/vexcode/vr** — a free browser-based virtual robot, no download
- Drive it manually, then program it to run a maze autonomously
- Use loops and sensor conditions
- **Milestone:** the robot completes a maze with no human input

### Week 4 — Tinkercad (does he like designing physical things?)
- **tinkercad.com** — free, Autodesk. Three tools in one: 3D Design, Circuits, Codeblocks
- Design a simple 3D object; then build a working LED circuit in Tinkercad **Circuits** (a full electronics simulator — you can burn out a virtual LED for free)
- **Milestone:** one 3D model + one working simulated circuit

### End of month: the diagnostic conversation
Ask him — and watch, don't just listen:

- **Which week did he lose track of time?**
- Which week did he ask to keep going past the timer?
- Which week did he show someone else what he made, unprompted?

That's where your money goes. If the answer is "none of them," that's real information too — robotics may be a passing interest, and that's completely fine at 10.

---

## 2. The roadmap: age 10 → 14

Four phases. Move on when the milestone is done, not when the calendar says so. Some kids take two years on Phase 1. Some blow through it in three months.

---

### Phase 1 — Blocks and first hardware
**Months 1–6 · roughly age 10**

**Goal:** The sense → decide → act loop becomes intuitive. He owns a robot that reacts to the physical world.

**Software**
- Continue Scratch; add **Code.org** CS Fundamentals, then CS Discoveries (free, [code.org](https://code.org))
- Move from Scratch to MakeCode blocks on real hardware

**Hardware — the first purchase (~$50–60)**
- **micro:bit v2** + **SparkFun Inventor's Kit for micro:bit v2**
- Why this and not a big LEGO kit: cheapest path to *real* sensors and motors; enormous free curriculum; block-coding now and MicroPython later on the same board, so the hardware doesn't become obsolete when his skills grow
- Free guides: **learn.sparkfun.com** (23+ micro:bit tutorials), **microbit.org** classroom resources, **learn.adafruit.com**

**Mechanical**
- Cardboard, hot glue, LEGO from the toy bin. Chassis design is a *design* skill, not a buying decision
- **4-H "Junk Drawer Robotics"** curriculum — build robots from household items, no computer required. Genuinely good, and free/cheap through your county extension office

**Math (15 min/day, Khan Academy)**
- Fractions, ratios and proportions, decimals, negative numbers, the coordinate plane, angles and area
- **Name the connection out loud every time:** a gear ratio *is* a fraction. A robot's heading *is* an angle. Its position on the field *is* a coordinate pair. This is the whole trick to making math feel non-optional.

**Milestone project:** a robot that reacts to the world — a line follower or an obstacle-avoider.

---

### Phase 2 — Text code and a team
**Months 6–12 · age 10–11**

**Goal:** He writes real code in a text editor, and he builds alongside other kids.

**Software — the big transition**
- MakeCode blocks → **MicroPython on the same micro:bit.** Same board, same projects, new language. This is the least painful blocks-to-text jump available
- **"Invent Your Own Computer Games with Python"** by Al Sweigart — free online at [inventwithpython.com](https://inventwithpython.com), and explicitly written to be understood by kids aged 10–12. This is the single best free Python book for his age
- Later: **"Automate the Boring Stuff with Python"**, also free at [automatetheboringstuff.com](https://automatetheboringstuff.com)

**Team** — see §4. This is the highest-value thing in the entire plan.

**CAD**
- Tinkercad → design a custom bracket or wheel, then print it. **Use your library's makerspace** rather than buying a printer (see §5)

**Math:** pre-algebra — variables, expressions, solving for x, unit conversion.

**Milestone project:** a robot with a custom part he designed in CAD and had manufactured (3D printed or laser cut).

---

### Phase 3 — Systems and intelligence
**Year 2 · age 11–12**

**Goal:** He moves from "a board that runs my code" to "a computer that perceives."

- **Hardware:** Raspberry Pi or ESP32. Networking, a camera, real compute. The **Elegoo ESP-32 Super Starter Kit** (~$36) or a Pi 5 are both good entry points
- **Software:** Python properly — functions, files, libraries. Introduce **Git** and version control. Real engineers version their work; starting at 11 is a superpower
- **Electronics:** breadboard → **soldering** (see §7 for safety). His first solder project should have 5–15 joints and visibly *do something* — light up, buzz, or move
- **Free projects:** **projects.raspberrypi.org** — 250+ free step-by-step projects from the Raspberry Pi Foundation
- **AI:** **Teachable Machine** ([teachablemachine.withgoogle.com](https://teachablemachine.withgoogle.com)) — train an image/sound/pose model with no code, in an afternoon. Then **Machine Learning for Kids** ([machinelearningforkids.co.uk](https://machinelearningforkids.co.uk)) to wire a trained model into a Scratch or Python project
- **Math:** Algebra 1 track

**Milestone project:** a robot that uses a camera or a model he trained himself.

---

### Phase 4 — Depth and identity
**Year 3 · age 12–13**

**Goal:** He stops being "a kid who does robotics" and becomes "a kid who is building *this specific thing*."

- **Pick a lane.** By now he'll lean mechanical, electrical, software, or AI. Let him specialize. Depth in one pillar plus literacy in the others is exactly how real engineers are shaped
- **CAD:** graduate Tinkercad → **Onshape** (real parametric, professional CAD; free education plan; note the age rules in §7)
- **Simulation:** **Webots** (free, open-source, industry-grade) and **robotbenchmark.net** — program simulated robots in Python in the browser. This is what university robotics actually looks like
- **Competition:** middle-school division. Consider VEX V5, or whatever FIRST's new K-8 program looks like by then (§4)
- **Math:** Algebra 2, geometry, intro trigonometry. **Trig is the gate.** Robot arms, turning geometry and kinematics are all trig. This is where kids get filtered out of robotics — not by losing interest, but by the math getting ahead of them
- **Portfolio:** publish. **Coolest Projects** (Raspberry Pi Foundation) is a free, worldwide, non-competitive showcase — an ideal first public demo

**Milestone project:** an original robot that solves a problem *he* chose, documented publicly.

---

## 3. The weekly rhythm

What actually works is **short and frequent, plus one long block.** Build sessions need setup and cleanup time; code sessions don't.

| When | Length | What |
|---|---|---|
| 2 weeknights | 45 min | Code, tutorials, simulator work |
| 1 weekend block | 2 hours | Physical building — needs the table and the mess |
| Every day | 15 min | Khan Academy math |
| Monthly | 30 min | **Demo night** — he shows the family what he built |

**Total: ~4–5 hours/week.** Resist going higher at this age. Over-scheduling is the number one way this ends.

**Demo night is not optional.** A recurring, low-stakes deadline is what converts "things I'm tinkering with" into "things I finished." It's also where he practices explaining technical work to non-technical people — which is, unglamorously, most of an engineer's actual job.

---

## 4. Competitions and clubs — *and why timing matters right now*

**Joining a team is the highest-leverage move in this entire document.** It supplies deadlines, peers, an adult who isn't you, and a reason to finish things. If you do only one thing from this plan, do this one.

### ⚠️ Time-sensitive: the FIRST LEGO League era is ending

This is genuinely important and most parents don't know it yet:

- **LEGO Education has not renewed its partnership with FIRST.** The **2026–27 season is the final FIRST LEGO League season.** (FIRST's 2026-27 season is branded **CANOPY**; the FLL Challenge portion is **BIOGLOW**, a biodiversity theme.)
- **The 2026-27 season is happening right now.** Kickoff was August 2026; tournaments run roughly November through February. If you want him to experience FLL at all, **this is the last chance, and teams are forming now.**
- After that: **LEGO Education launches "LEGO League"** in August 2027, and **FIRST launches its own new K-8 programs** in 2027. Both are unproven.

**What this means for your wallet:** don't sink $300–400 into a LEGO SPIKE Prime primarily as a *competition* investment. The 2027-28 LEGO League season will support SPIKE and legacy hardware, but from 2028-29 the program moves solely to LEGO Education's new Computer Science & AI platform. SPIKE Prime is still an excellent teaching kit — just don't buy it as a competition-pipeline bet.

**VEX has announced no such discontinuity.** For a 10-year-old planning multiple years, **VEX IQ is the more future-stable competition platform.**

### The options

| Program | Ages / grades | Rough cost | Notes |
|---|---|---|---|
| **VEX IQ** (VIQRC) | Elementary = below 6th grade | Kit ~$400+, plus registration & events | **2026-27 game: "Level Up."** Most future-stable. He's elementary division; elementary students *may* play up to middle school |
| **FIRST LEGO League Challenge** | Ages 9–16 (~grades 4–8) | ~$285 registration + challenge set + event fees | Final season ever. Season underway now |
| **4-H Robotics** | Varies | ~$20–100/yr | **Cheapest real club.** Strong in rural and farming communities. Contact your county extension office |
| [**SeaPerch**](https://seaperch.org/) | Middle school+ | Low | Underwater ROV. Superb hands-on build, very different flavor |
| [**Robofest**](https://www.robofest.net/) | Elementary+ | ~$100 | Autonomous robots, platform-agnostic |
| [**RoboRAVE**](https://www.roborave.org/) / [**National Robotics Challenge**](https://www.thenrc.org/) | Varies | Low–moderate | No required kit — build from anything |
| [**Wonder League**](https://www.makewonder.com/robotics-competition/) | Elementary & middle | Low | Good entry point for younger kids |
| **Code Club / CoderDojo** | 7–17 | **Free** | Raspberry Pi Foundation. Free coding clubs worldwide |
| [**Coolest Projects**](https://coolestprojects.com) | Any | **Free** | Showcase, not a competition. Great first public demo |

### How to find something local
1. **Call your county 4-H extension office.** Cheapest path to a real club, and they'll know what else exists locally
2. Search **firstinspires.org** and **robotevents.com** for teams near you
3. Ask his school — many have teams that don't advertise
4. Check the **public library** — many run makerspaces and clubs
5. **NASA's Robotics Alliance Project** ([robotics.nasa.gov/robotic-competitions](https://robotics.nasa.gov/robotic-competitions/)) maintains a competition directory

### If there's no team near you
**Start one.** Both FLL and VEX support new teams — you need 2–10 kids and one adult coach. **You do not need to know robotics to coach.** You need to book a room, keep a schedule, and ask good questions. The kids figure out the robot. Recruit two other families and you have a team.

---

## 5. The budget ladder — spend on evidence, not hope

The most common and most expensive mistake is buying Tier 3 first. **A $400 kit does not create interest. It creates guilt** — his, for not using it, and yours, for having bought it.

Each tier has a **gate.** Don't move up until the gate is met.

| Tier | Cost | What | **Gate to unlock** |
|---|---|---|---|
| **0** | **$0** | The 30-day kickstart (§1). Scratch, MakeCode, VEXcode VR, Tinkercad | Start here. No exceptions. |
| **1** | **~$50–60** | micro:bit v2 + SparkFun Inventor's Kit | He finished the 30 days and *asked* for more |
| **2** | **~$100–160** | Motors & chassis (micro:bot kit), or Elegoo UNO Basic Starter (~$20) / ESP-32 Super Starter (~$36) / Smart Robot Car V4 (~$76) | He completed 3+ hardware projects **without being prompted** |
| **3** | **~$300–500** | Team registration + competition kit (VEX IQ or SPIKE Prime), or a 3D printer | Sustained 6+ months, and he wants to compete |
| **4** | **Your time** | Driving to meetings, sitting through tournaments, learning alongside him | This is the real investment, and it's the one that actually matters |

### Ways to spend less
- **Library makerspaces** — 3D printing, laser cutting, often free or near-free. Use these instead of buying a printer for at least the first two years
- **School STEM lab** — ask what's sitting unused
- **Borrow from a local team** — teams often have spare kits between seasons
- **Buy used** — VEX IQ and LEGO kits hold up well and turn over on secondhand markets when teams graduate
- **Financial aid** — most competitions offer it, and most fundraise. Ask; it's normal and expected

---

## 6. The math track — the part everyone skips

**Kids don't quit robotics because they stop liking robots. They quit because the math got ahead of them.** Robotics engineering is applied mathematics with a battery attached.

Fifteen minutes a day on Khan Academy (free) is enough. The dose matters less than the consistency.

| Age | Topics | Why it's robot math |
|---|---|---|
| **10–11** | Fractions, ratios, proportions, decimals, negatives, coordinate plane, angles, area | Gear ratios *are* fractions. Field position *is* coordinates. Turning *is* angles |
| **11–12** | Pre-algebra: variables, expressions, solving equations, unit conversion | A variable in code and a variable in algebra are the same idea |
| **12–14** | Algebra 1, geometry, intro trigonometry | **Trig is the gate.** Arms, turning geometry, kinematics |
| **14+** | Algebra 2, precalculus, calculus, linear algebra, physics | Control theory, computer vision, dynamics |

**The technique that makes this work:** every time he hits a robot problem, name the math out loud.

> *"Your robot overshoots the line by about 20% every time. That's a ratio problem — what if we scaled the motor power by the same fraction?"*

Do that a hundred times and math stops being a school subject and becomes a tool he reaches for.

---

## 7. The parent playbook

### The single highest-leverage thing you can do: don't fix his bugs

When he's stuck, you will know the answer before he does. **Do not say it.** Ask these five questions instead — this is the debugging ritual, and it is the entire career in five lines:

1. **What did you expect to happen?**
2. **What actually happened?**
3. **What's different between those two?**
4. **What's the smallest test that tells you which part is wrong?**
5. **Change one thing. Test it. Repeat.**

A 10-year-old who internalizes this is doing what professional engineers do all day. A 10-year-old whose dad fixes the robot has a working robot and no skill.

### Rules of thumb
- **Let him choose the projects.** Interest beats curriculum, every time
- **Never say "that's too hard," and never say "I was bad at math."** Kids inherit that instantly and permanently
- **Ship small, ship often.** A five-line program that makes a sprite dance today beats an ambitious robot that's still half-built in March
- **Document everything.** Photos, a build journal, short videos. A three-year portfolio at age 13 is genuinely extraordinary — for scholarships, for programs, and for his own sense of momentum
- **Learn alongside him.** You do not need to know any of this. "I don't know, let's find out" is the correct and best answer
- **Take breaks.** A walk around the block resets a frustrated kid faster than another 20 minutes of trying
- **Celebrate the failures that taught something.** The robot that caught fire is a better story and a better lesson than the one that worked first try

### Know the difference between two kinds of frustrated
- **Frustrated and leaning in** — jaw set, still trying things. *Sit with him. Don't touch anything. This is learning.*
- **Frustrated and shutting down** — pushing the robot away, "this is stupid." *Stop. Snack, walk, come back tomorrow. Pushing through this one costs you months.*

### Warning signs, and how to adapt
| What you see | What to do |
|---|---|
| Only wants to build, never code | Fine. Lean mechanical. Code will arrive when a build needs it |
| Only wants to code, never build | Fine. Use simulators (VEXcode VR, Webots). Hardware can come later |
| Interest drops for 3+ weeks | **Back off completely.** Don't push, don't guilt. Interest usually returns if it isn't forced. Pressure is what kills it permanently |
| Races ahead of the plan | Let him. Skip phases. Get him onto a team with older kids as fast as possible |
| Wants to quit entirely | Let him, cleanly and without disappointment. He's 10. The skills transfer to whatever's next |

---

## 8. Safety

**Soldering** — appropriate from around age 10 with close supervision. Readiness is about fine motor control and maturity with hot tools, not birthdays.
- Lead-free solder
- Ventilated area or a fume fan
- Safety glasses, always
- **Iron always returns to the stand** — enforce this absolutely, from the first minute
- First project: 5–15 through-hole joints, and it must visibly work when finished

**Electrical** — battery and USB voltages only. No mains wiring. Never leave LiPo batteries charging unattended.

**Tools** — safety glasses for any cutting or drilling. An adult operates anything that spins fast.

**3D printers** — hot ends and heated beds cause real burns. Supervise, and ventilate.

**Online accounts (COPPA)** — under-13 accounts on Scratch and Tinkercad need parent setup. **Onshape requires 13+**, or a school/qualified adult authorizing the account. Check each platform's under-13 policy as you go.

---

## 9. His first five projects

Concrete, in order. Each one: build it, break it, fix it, and film a 30-second demo.

1. **Reaction timer** (micro:bit, blocks) — input, timing, display
2. **Line-following robot** (micro:bit + motor board) — sensors and a control loop
3. **Obstacle-avoiding rover** — decision logic and state
4. **A custom 3D-printed bracket for the rover** (Tinkercad) — CAD, tolerances, iteration
5. **AI-triggered robot** (Teachable Machine → controls the robot) — what modern robotics actually is

---

## 10. Free resource directory

Everything here is genuinely free.

### Programming
| Resource | URL | Notes |
|---|---|---|
| Scratch | [scratch.mit.edu](https://scratch.mit.edu) | MIT. The universal starting point |
| CS50 Scratch | [cs50.harvard.edu/scratch](https://cs50.harvard.edu/scratch) | Harvard, free, gentlest real CS intro |
| Code.org | [code.org](https://code.org) | CS Fundamentals + CS Discoveries, full free curriculum |
| Khan Academy | [khanacademy.org](https://www.khanacademy.org) | Math *and* intro programming |
| Invent With Python | [inventwithpython.com](https://inventwithpython.com) | Al Sweigart's books, free under Creative Commons. *Invent Your Own Computer Games* is written for ages 10–12 |
| Automate the Boring Stuff | [automatetheboringstuff.com](https://automatetheboringstuff.com) | Free online, the practical follow-on |
| CS Unplugged | [csunplugged.org](https://www.csunplugged.org/en/) | Computer science with no computer — cards, string, running around |

### Robotics & electronics
| Resource | URL | Notes |
|---|---|---|
| micro:bit MakeCode | [makecode.microbit.org](https://makecode.microbit.org) | **Built-in simulator — no hardware needed** |
| micro:bit Foundation | [microbit.org](https://microbit.org) | Free lessons and classroom activities |
| SparkFun Learn | [learn.sparkfun.com](https://learn.sparkfun.com) | Excellent free tutorials, 23+ on micro:bit alone |
| Adafruit Learning System | [learn.adafruit.com](https://learn.adafruit.com) | Deep, well-written electronics guides |
| Raspberry Pi Projects | [projects.raspberrypi.org](https://projects.raspberrypi.org/en/projects) | 250+ free step-by-step projects |
| Tinkercad | [tinkercad.com](https://www.tinkercad.com) | Free 3D design + a full circuit simulator + Codeblocks |

### Simulators (robotics with zero hardware)
| Resource | URL | Notes |
|---|---|---|
| VEXcode VR | [vexrobotics.com/vexcode/vr](https://www.vexrobotics.com/vexcode/vr) | Browser-based virtual robot. Blocks → Python |
| Webots | [cyberbotics.com](https://cyberbotics.com) | Free, open-source, used in industry and research |
| robotbenchmark | [robotbenchmark.net](https://robotbenchmark.net) | Webots in the browser, Python, free challenges |
| Gears / GearsBot | search "GearsBot simulator" | Blocks → auto-converts to Python |

### AI
| Resource | URL | Notes |
|---|---|---|
| Teachable Machine | [teachablemachine.withgoogle.com](https://teachablemachine.withgoogle.com) | Google. Train a model in an afternoon, no code |
| Machine Learning for Kids | [machinelearningforkids.co.uk](https://machinelearningforkids.co.uk) | Wire trained models into Scratch and Python |

### CAD
| Resource | URL | Notes |
|---|---|---|
| Tinkercad | [tinkercad.com](https://www.tinkercad.com) | Start here |
| Onshape Education | [onshape.com/en/education](https://www.onshape.com/en/education/) | Free education plan. Professional parametric CAD. 13+, or adult-authorized |

### Clubs & competitions
| Resource | URL | Notes |
|---|---|---|
| Code Club | [codeclub.org](https://codeclub.org) | Free clubs worldwide |
| CoderDojo | Raspberry Pi Foundation | Free, ages 7–17 |
| 4-H Robotics | [4-h.org/programs/robotics](https://4-h.org/programs/robotics/) | Contact your county extension office |
| FIRST | [firstinspires.org](https://www.firstinspires.org) | FLL and beyond |
| RECF / VEX | [recf.org](https://recf.org), [robotevents.com](https://www.robotevents.com) | Find local VEX events and teams |
| NASA Robotics Alliance | [robotics.nasa.gov/robotic-competitions](https://robotics.nasa.gov/robotic-competitions/) | Competition directory |

---

## 11. What to do this week

1. **Tonight:** open [scratch.mit.edu](https://scratch.mit.edu) together and make something for 30 minutes. Nothing else.
2. **This week:** start the 30-day kickstart (§1). Put the four weeks on the calendar.
3. **This week, in parallel — this one is time-sensitive:** call your county 4-H extension office, and search [robotevents.com](https://www.robotevents.com) and [firstinspires.org](https://www.firstinspires.org) for teams near you. **The 2026-27 season is already underway and it's the last FLL season ever.** Teams form in August and September.
4. **Start the 15-minutes-a-day Khan Academy habit now.** It compounds, and it's the thing that's still paying off in six years.
5. **Buy nothing** until the 30 days are done.

---

*Sources: firstinspires.org, LEGO Education, VEX Robotics / RECF, Raspberry Pi Foundation, SparkFun, Al Sweigart / Invent With Python, Autodesk Tinkercad, Onshape, National 4-H Council, NASA Robotics Alliance Project, Harvard CS50, Code.org, CS Unplugged, Google Teachable Machine. Researched September 2026 — verify prices and season dates before committing.*
