## What and why
<!-- Short summary. Closes #... -->

## How to test
<!-- Commands or steps a reviewer can run. -->

## Checklist
- [ ] Lint passes
- [ ] Typecheck passes
- [ ] Tests pass
- [ ] New tests cover unauthenticated access, another user's data and invalid input (if it touches the API or DB)
- [ ] No secrets or real values committed; only `.env.example` changed
- [ ] RLS stays enabled; no policy was widened
- [ ] Nothing from `private/` is included
- [ ] New dependencies were approved and added to `docs/dependencies.md`
- [ ] No personal data in logs or LLM calls
