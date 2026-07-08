---
type: research
id: rn-un-represent-ability
status: draft
created: 2026-07-03
updated: 2026-07-03
links: []
supersedes: null
superseded_by: null
warrant: null
---

# Executive Summary  
Strong type systems and formal methods can **eliminate entire classes of bugs** by construction – a philosophy often summed up as “make illegal states unrepresentable”.  In practice this means using language features (e.g. option types, algebraic unions, dependent/refinement types) and verification tools so that invalid combinations simply *cannot* be coded.  Advocates (and even U.S. government cybersecurity agencies) argue this dramatically improves security: for example, Microsoft reports that ~70% of its tracked security bugs are memory-safety issues that *Rust’s* compile-time checks would prevent.  Formal languages like F* carry proofs of security properties, and verified kernels like seL4 eliminate entire vulnerability categories.  

However, experts caution that **over-constraining designs can backfire**. Too many invariants can complicate code, hinder flexibility (requiring expensive redesigns for edge cases), or produce a “cathedral of phantom types” that’s unmaintainable. Large firms often accept some “illegal” states (e.g. no foreign-key constraints) for practical agility. Moreover, unrepresentable-state guarantees only hold up to trust boundaries; dynamically loaded plugins or AI-generated code that bypass static checks can reintroduce invalid states.  

**Conclusion:** In general, shifting checks into the type system and design (making bad states unrepresentable) is *highly useful* for catching many vulnerabilities early, but it is not a silver bullet. A balanced approach—strong static invariants for core components plus careful boundary validation and runtime containment—is recommended.  We survey key concepts, tools, and trade-offs below, with comparisons (see Tables) and diagrams illustrating system architectures and threat flows.  

## Definitions & Taxonomy of “Unrepresentable” States  
- **Illegal vs. unrepresentable.**  An *illegal* state is a runtime condition that violates a rule (e.g. an out-of-bounds index, null reference, or invalid enum value) that must be guarded against. An *unrepresentable* state is one the program *cannot even encode* in its types or logic. For example, using a typed union (`enum`/variant) to represent mutually exclusive options means contradictory combinations are simply untypeable.  

- **Type-system enforcement.** Modern type systems support many features to encode invariants. *Discriminated unions* (algebraic data types) force exhaustive handling and forbid impossible tag combos. *Phantom types* or refinement types can tag data (e.g. “sanitized” vs “raw”) so the compiler won’t mix them. *Linear/affine types* (Rust’s ownership, or Haskell’s linear types) ensure resources are used exactly or at most once, preventing leaks or races. *Dependent types* (F*, Idris, Agda) allow types to depend on values, so you can encode numeric bounds or protocol states in the type itself, provably excluding invalid cases. *Effect systems* and *capabilities* add context (e.g. “read-only” vs “read-write” handles) to prevent unauthorized operations by type.  

- **Formal methods.**  Beyond type theory, formal verification (model checking, theorem proving) takes the principle further: programs must carry proofs that no “bad” execution is possible. *Proof-Carrying Code* (Necula) requires untrusted code to present a formal proof of safety before execution. Verified kernels like seL4 have machine-checked proofs that every access-control and memory operation respects strict invariants. In these cases, any attempt to violate a guarantee is literally **impossible** in the compiled binary.  

- **Language/runtime features.**  Some languages enforce invariants at runtime. For example, Ada/SPARK uses contracts and a verifier to prevent undefined behavior; array bounds and division-by-zero can be disallowed at compile time. In capability-based systems (e.g. Capsicum, seL4, CHERI), the hardware/OS *caps* ensure that illegal permission combinations are not representable. Sandboxed runtimes (JVM, WebAssembly, or SES/Jessie for JS) make certain memory states and privilege escalations impossible.

## Theoretical Foundations  
- **Type theory & substructural types.**  Modern type systems are grounded in formal type theory. Rust’s borrow checker is effectively an *affine type system*: values can be “used at most once,” giving compile-time memory safety (no dangling pointers or races) without a GC. Pure linear types enforce *exactly* once usage, solving resource leaks and races trivially (but requiring burdensome plumbing, hence Rust’s “borrowing” relaxation). Dependent types (in Coq/Agda/F*) generalize this: you can write `Array<n>` where `n` is a compile-time Nat, preventing out-of-bounds or null in the type. The seminal F* language uses a **kind system** to mix linear, pure, and effectful code, enabling proofs about stateful programs.  

- **Proofs and logic.**  Type theory links closely to logic (Curry-Howard). Refinement types and SMT-based checkers (Liquid Haskell, F*, Dafny) encode invariants as logical predicates that must hold. Proof-carrying code and certifying compilers embody the idea of *executable proofs*: each program comes with a proof that it meets a safety policy (for memory, type safety, or domain rules). The verifier then statically guarantees no “illegal” flows exist. While theoretically powerful, generating these proofs remains expensive, so such methods are mostly used in high-assurance niches (e.g. cryptography protocols, critical kernels).  

- **Effect systems.**  Some languages (like Koka, Frank) track side-effects in types. By making effects (I/O, exceptions) explicit in types, the language can forbid certain bad interactions. For instance, a type may say “does not perform I/O,” making any attempt to perform forbidden actions untypeable. This is similar philosophically to “unrepresentable states”: if a function’s type excludes producing an error, you remove the possibility of that error state entirely.  

- **Temporal and information-flow types.**  Advanced systems use *temporal or linear logic* types for properties like absence of deadlock or constant-time execution. For example, linear logic can encode single-threaded access to a resource. Information-flow type systems (e.g. Jif, FlowCaml) prevent confidential data leaking into public channels, effectively making “tainted” data flows unrepresentable. These are part of the broader set of theoretical tools for security by design.  

## Practical Patterns and Tools  

| **Language/Tool**       | **Safety Guarantees**                              | **Overhead/Limitations**                      | **Maturity/Adoption**                   |
|------------------------ |----------------------------------------------------|----------------------------------------------|-----------------------------------------|
| **Rust**                | *Memory-safe*, no nulls, no data races (by default). Ownership & borrowing ensure use-after-free and race conditions are impossible in safe code. | Steep learning curve; *`unsafe`* blocks required for low-level tasks; interoperability with C++/GC languages can be tricky. Compile times can be high for complex generics. | Rapidly growing. Used by Mozilla, Microsoft, Google (Android), and in Linux kernel components. MS reports ~70% of its past security bugs would be eliminated under Rust. Strong community & tooling. |
| **Haskell/OCaml/F#**    | Pure functional, strong types. No null (uses `Maybe`/`Option`), no implicit type coercion, exhaustive pattern matching. Enforces *algebraic invariants*. | Garbage collected (not always ideal for hard real-time); lazy evaluation can be confusing. Less mainstream in systems contexts; libraries for side-effect controls (monads) add complexity. | Mature academically and in finance/blockchain (Cardano’s Haskell code). Less use in OS, but used in some security tools (Cryptol). Reliable compilers exist (GHC, OCaml compiler). |
| **Ada/SPARK**          | Strong typing, mandatory runtime checks (or proven absence), contracts. SPARK is verifiable Ada subset: statically checks absence of overflow, index errors, nulls, etc. Supported by static analysers (GNATprove). | Verbose syntax; learning curve for Ada, even steeper for SPARK. Targets embedded/safety-critical niche. Not suited for high-performance general-purpose tasks (though quite fast). | Proven in aerospace, defense, rail, and medical devices (e.g. Airbus, nuclear control). Industry-grade tools (GNAT). Certified safety-critical use (DO-178C, etc). |
| **F\***                 | Full dependent types plus effect system for crypto/protocol proofs. Can verify complex security properties and extract to executable code. | Experimental; heavy-weight. Significant proof effort needed, plus runtime overhead (increased code size 60% for proofs). Not mainstream; mostly MSR/academic use. | Used in Microsoft’s Project Everest (verified TLS and crypto libraries), and some web security proofs. Tooling improving but still research-grade. |
| **TypeScript/Flow**     | Static type checking for JavaScript. Helps catch many type errors at compile time. Enforces declared interfaces/nominal types. | Types erased at runtime; unsafe casts possible. Must still guard at runtime (e.g. JSON parsing). Only as strong as type declarations. Good but not foolproof. | Very widely adopted for web apps. Tooling good. But security relies on additional runtime checks, since JS semantics are still open at runtime. |
| **Static Analyzers** (Coverity, CodeQL, etc.) | Find common patterns (null deref, buffer overflow, SQL injection) via heuristics.  | Not sound: may miss edge cases or give false positives. Not guaranteed to enforce invariants globally. | Extensively used in industry for C/C++/Java/etc. Can catch bugs that slip through tests, but require configuration and maintenance. |
| **Model Checking (TLA+, Alloy, SPIN)** | Exhaustively check protocol or system models for safety/liveness properties before coding. Finds subtle design bugs (e.g. race conditions) at high-level. | Not applied to full code – designers must create abstract model. Learning curve. | Used by AWS, Microsoft, NASA to find bugs in distributed systems (TLA+ on S3, Azure). Not widespread in small teams. |
| **Contracts/DbC (Eiffel, D, Frama-C)** | Runtime preconditions/postconditions/invariants. Makes assumptions explicit and checks them in debug builds. | Only checked at run/test time (can be stripped in production). Requires discipline to write and maintain. | Used in academia and select projects. Eiffel languages popular historically. SPARK uses contracts + static checking. |
| **Sandboxing/VMs** (Containers, SES, eBPF) | Constrain code to limited APIs. Even if code is "bad", damage is contained. Unreachable states become irrelevant since code can’t exercise them. | Doesn’t *prevent* bugs inside sandbox, only isolates them. Performance overhead for full OS VMs. Engineering overhead. | Ubiquitous (containers, seccomp, WebAssembly). Standard practice for isolating untrusted code/extensions. |
| **Capability-based OS** (seL4, Genode, Capsicum) | OS-level capabilities strictly bound permissions: e.g. a process with no disk-cap can never corrupt disk. Certain illegal operations (like accessing unauthorized memory) are unrepresentable. | Newer, specialized OSs. Requires rethinking of architecture. Not backward-compatible with all existing apps. | Used in high-security domains (DARPA, defence). The seL4 kernel is fully formally verified; Genode is a research OS microkernel. |

Many real-world security practices blend these approaches. For example, a microservice might be written in Rust (memory-safe core) with a small unsafe shim for I/O; inputs are parsed (not just validated) at the network boundary; and plugins or scripts run in a locked-down sandbox.  

## Industry Adoption & Case Studies  
- **Memory-safe languages in industry.**  Government and industry reports emphasize shifting to memory-safe languages to reduce vulnerabilities. Google, Microsoft, Facebook, and others have begun adopting Rust for critical components (e.g. parts of Android, Windows, and Linux kernel) largely for security reasons. Microsoft’s own analysis found “70% of the security issues…are memory safety issues,” implying the bulk could vanish under Rust.  Similarly, Rust-based initiatives (e.g. Cloudflare’s BoringSSL fork, AWS Firecracker VMM) report fewer critical bugs.  

- **Formal methods successes.**  While rarer, there are notable successes. The seL4 microkernel (C/F* verified) provides *end-to-end proofs* of correctness and security, yielding a system where many exploit classes simply **do not exist**. Formal methods have prevented logic flaws: Amazon attributes TLA+ to finding subtle bugs in its systems before deployment. Verified cryptography stacks (CompCert, F* Everest) ensure no low-level errors slip into crypto libraries. These are often closed or academic projects, but they demonstrate feasibility at high assurance levels.  

- **Cases of unrepresentable-state preventing bugs.**  Several CVEs are classic examples. *Heartbleed* (OpenSSL) was an out-of-bounds read in C; as one expert notes, “Heartbleed is rooted in C not being memory safe. Rust is. You will not see vulnerabilities like Heartbleed… in Rust”. While we lack a formal CVE saying “would be prevented by X,” many security bulletins (e.g. MSRC notes) highlight that common issues like buffer overflows or use-after-free (CWE-119/122) are largely mitigated by Rust/GC languages. Conversely, allowing “mostly correct” invariants can still fail: Tony Arcieri calls a Rust demo “Tedbleed” (a strawman) to show that even safe languages can have design flaws if misuse of APIs occurs.  

- **Balance with flexibility.**  Industry experience also shows the limits. Sean Goedecke observes that over-strict schemas (e.g. enforced foreign keys, rigid state machines) can hinder development and require complex workarounds for real-world exceptions. For example, GitHub and Zendesk avoid database foreign keys to allow more flexible migrations. These examples illustrate trade-offs: constraints should match truly invariant properties; otherwise they create engineering friction without commensurate security gain.  

- **Supply chain & AI-generated code.**  A growing concern is that heavy static typing doesn’t automatically apply to dynamically fetched or AI-generated code. The “Parse, don’t validate” rule emphasizes that any untrusted boundary (including dependencies, CI pipelines, or AI code suggestions) is a trust boundary. Malicious or buggy third-party modules can introduce invalid states even if the core language is safe. For instance, a Trojanized npm package might subvert invariants (everything a project “ships under your name” must be vetted). Similarly, AI tools could produce code that violates domain invariants unless integrated into the same type-checking discipline (which rarely happens). Thus, organizations treat dependencies as untrusted input, pinning and auditing them, and sandboxing AI-generated code to contain unexpected states.  

## Limitations, Trade-offs, and Ergonomics  
- **Developer overhead.**  Encoding rich invariants in types often adds complexity. Pure linear types solve memory safety trivially, but as Borretti notes, “linear types are very onerous to write… you’d have to thread use-once variables through function calls. Nobody wants to write code like this”. Rust’s ownership/borrow system is essentially a practical relaxation of linear types for usability. Likewise, heavy use of phantom types or intricate unions can lead to very complex type signatures (“the cathedral of phantom types nobody can read”), hurting maintainability. Even in functional languages, overly creative type tricks can obscure intent and slow new developers.  

- **Performance.**  Statically checked invariants can impose runtime or compile costs. Runtime checks (e.g. range checks in Ada or contracts in Eiffel) incur overhead, though usually modest. Dependently typed proofs often increase code size significantly (the F* compiler reports ~60% code-size overhead for carrying proofs). Worst-case static analysis or model checking can be extremely slow for large codebases. In practice, teams must balance the level of static checking with acceptable build times.  

- **Flexibility & Evolution.**  Overly rigid representations can make future changes expensive. Sean Goedecke warns that “your code should be more flexible than your domain model”. Real-world domains change, and accommodating new requirements (e.g. a new “hotfix” transition in a state machine) may require revisiting core types, bloating them with exceptions. As a rule, it’s often better to model *main invariants* strictly and allow some fallback paths, rather than try to encode every conceivable rule. Static invariants should not become immovable constraints that block legitimate change.  

- **Shifted attack surface.**  Even in strongly-typed code, bugs still occur, but they shift category. Memory-unsafe bugs drop (Rust/C#/Java, etc.), but logic errors, protocol flaws, and misuse of safe APIs remain. For example, Rust eliminates buffer overflow and null deref, but you can still have SQL injection if you blindly concatenate strings. In verified code, mis-specified proofs or wrong formal assumptions are risks. Attackers also target the verification infrastructure or compilers (the “trusted computing base” expands). Essentially, making states unrepresentable *raises the bar* but does not close the door entirely.  

- **Complex ecosystems.**  Integrating unrepresentable-state techniques into large or third-party ecosystems is hard. If part of the system is written in an untyped or dynamic language (legacy C, Python scripts, GPU kernels, etc.), it can violate invariants assumed by typed components. Mixed-language projects must either restrict such components heavily or carefully define interop boundaries. For example, Java’s `null` largely disappears from Kotlin code (Kotlin makes null unrepresentable in its type system), but any Java library that returns null violates that invariant at the boundary. These practicalities mean teams often apply “unrepresentable” design to new code while dealing with legacy via wrappers or runtime checks.  

## Recommendations & Best Practices  

1. **Enforce invariants at boundaries (“Parse, don’t validate”).** Treat *all* inputs from outside (users, network, dependencies) as untrusted. At each trust boundary, parse or convert data into a *narrow type* that by construction meets your invariants. Downstream logic can then assume correctness without repeated checks. For example, use strong DSL parsers or schema validators that only return a rich typed object on success.  

2. **Use strong type features where it matters most.** Identify critical invariants (e.g. user IDs must never be negative, or a machine only in one state at a time) and encode them in types (enums, newtypes, refinement checks). Languages like Rust or Ada are excellent for core safety-critical modules. For transient glue code or config, more flexibility (e.g. runtime asserts) may suffice.  

3. **Limit the scope of “unsafe” or unchecked code.** If you must drop into low-level code (e.g. C bindings, `unsafe` Rust), isolate it in small modules with careful review and testing. The smaller the trusted core, the better. As Microsoft notes, marking unsafe blocks explicitly dramatically reduces the code surface needing manual inspection.  

4. **Invest in static analysis and formal checks.** Use linters, static analyzers, or contract checkers for properties that types can’t express easily (e.g. complex data-flow invariants, memory leaks). For security-critical algorithms, consider model checking or interactive proofs (TLA+, Coq) if resources allow. Even simple tools (dependabot security alerts, taint analyzers) help maintain invariants.  

5. **Monitor and sandbox at runtime.** Because not all bad states can be eliminated statically, implement defense-in-depth. Sandboxing (containers, eBPF, WebAssembly runtimes) can contain unforeseen bad-behavior modules. Runtime intrusion detection (like memory sanitizers or monitors) may catch what compile-time missed. Also, keep diverse barriers: e.g. apply OS-level CFI/ASLR in addition to language safety.  

6. **Gradual adoption with compatibility.** When migrating existing projects, consider “memory-safe roadmaps”: start new modules in safer languages, progressively replace hotspots (network parsers, crypto). Use FFI carefully, and allow mixed code with strict interfaces. In large teams, establish coding standards that reinforce invariants (e.g. non-null types, immutable data by default, capability-based libraries).  

7. **Handle dependencies cautiously.** Treat third-party code as another form of untrusted input. Pin versions, audit critical libraries, and prefer ones written in safe languages or those that enforce invariants. For AI-generated code or plugins, consider running them in a monitored environment or with formal specification adherence.  

8. **Balance strictness and pragmatism.** Not every “bad state” need be unrepresentable. If an invariant is likely to change, consider runtime checks or documented hacks instead of baking it into the type system. The goal is to **reduce the *blast radius* of invalid inputs** (see Fig. below): catch what you can in types, but accept that some flexibility is needed, and make sure failures are contained.  

## Illustrative Diagrams  

```mermaid
flowchart LR
  Attacker((External Attacker)) -->|Crafts input| Boundary([Parse/Validate Input at Boundary])
  Boundary -->|Valid data| TypedData((Typed, Safe Data))
  Boundary -->|Invalid| Reject[/Reject Request/]
  TypedData -->|Feeds| CoreLogic((Core Business Logic))
  TypedData -->|Passes to| Plugin([Third-Party Module (Sandboxed)])
  CoreLogic -->|Produces| GoodState((Safe System State))
  Plugin -->|Malicious or buggy| Compromise((Possible Violation))
  Attacker -.->|Targets| Compromise
  classDef gray fill:#f9f9f9;
  class Boundary,TypedData,CoreLogic,GoodState gray
```
*Figure: A simple threat flow. Inputs from an attacker are parsed into well-typed data; valid data flows into core logic, yielding a safe state. Third-party code or plugins (possibly malicious) can bypass some invariants, potentially leading to unsafe states unless sandboxed. Stop invalid inputs at the boundary and isolate untrusted modules.*  

```mermaid
flowchart TB
  subgraph System
    A1[API Server (Rust)] 
    A2[Database (SQL)] 
    A3[Scheduler (Haskell)] 
    A4[Plugin Engine (JS)]
  end
  subgraph OS
    OS([Host OS Kernel])
  end
  Attacker((Attacker)) -->|Network| A1
  A1 --> A2
  A1 --> A3
  A3 --> A2
  Attacker -->|Malicious Plugin| A4
  A4 -->|Limited| A1
  A1 --> OS
  A2 --> OS
  A4 --> OS
```
*Figure: A sample system composition. Core services (Rust, Haskell) enforce strong types and invariants, while a plugin engine (JS) is sandboxed. An attacker can send crafted requests or malicious plugin code, but memory-safe languages (Rust, Haskell) and OS sandboxing limit the damage.*  

## Conclusion  
“Make illegal states unrepresentable” is a **powerful security principle** when applied judiciously. It shifts error detection to compile time and removes whole vulnerability classes by design. Industry experience (Microsoft’s 70% stat, NSA/CISA reports, etc.) strongly supports using strong type systems and memory-safe languages for security-critical code. However, our review also finds that it is **not universally obvious or free**: it imposes design and maintenance costs. Successful secure systems often combine unrepresentable invariants *with* conventional checks: parse all external inputs into safe types, use static analysis/verification on hot code, and sandbox or audit anything outside the core. In practice, aim to *push* as many guarantees as possible into types and proofs, but maintain “escape hatches” and fallbacks where rigidity would stifle correctness or evolution. 

**Best practice:** enforce critical invariants in code (using types or formal proofs) wherever feasible, and validate at trust boundaries. Recognize the limits: if you overload the type system with every nuance, readability and agility suffer. In the end, a *hybrid approach*—static typing for core guarantees, dynamic checks for real-world variability, and strict compartmentalization for untrusted code—yields the most robust security posture.  

**Sources:** We have drawn on academic papers and industry reports on type systems and security, language documentation (Rust, SPARK), and expert blog posts and case studies. Each cited source is linked above.

