const intake = await agent("Conduct intake for ID={ticketId}");

const questions = await agent(
  prompt(
    "Review intake for helpdesk ticket {ticketId}. Decide whether missing information blocks safe diagnosis or implementation. Ask only necessary concrete questions.\n\n{intake}",
    { ticketId: args.ticketId, intake },
  ),
  {
    outputSchema: {
      type: "object",
      properties: {
        needsClarification: { type: "boolean" },
        questions: { type: "array", items: { type: "string" } },
      },
      required: ["needsClarification", "questions"],
      additionalProperties: false,
    },
  },
);

if (questions.needsClarification && !args.clarification) {
  const proceed = await checkpoint({
    name: "intake-clarification",
    prompt: "Answer these intake questions, then resume workflow with clarification text in args.clarification.",
    context: { ticketId: args.ticketId, questions: questions.questions },
  });
  if (!proceed) return { intake, questions, status: "awaiting-clarification" };
  return { intake, questions, status: "resume-with-clarification" };
}

const finalizedIntake = await agent(
  prompt(
    "Finalize intake for helpdesk ticket {ticketId}. Incorporate clarification below. Return complete reproduction facts, scope, constraints, and success criteria. Do not diagnose or edit files.\n\nInitial intake:\n{intake}\n\nClarification:\n{clarification}",
    { ticketId: args.ticketId, intake, clarification: args.clarification || "None needed" },
  ),
);

const diagnosis = await agent(
  prompt(
    "Diagnose helpdesk ticket {ticketId} using finalized intake below. Trace the full Odoo flow, inspect relevant addons and shared sources, and propose the smallest root-cause fix. Do not edit files.\n\n{finalizedIntake}",
    { ticketId: args.ticketId, finalizedIntake },
  ),
);
const implementation = await agent(
  prompt(
    "Implement ticket {ticketId} using diagnosis below. Follow project instructions. Make minimal changes, add/update focused tests, and report changed files.\n\n{diagnosis}",
    { ticketId: args.ticketId, diagnosis },
  ),
  { isolation: "worktree" },
);

const validation = await agent(
  prompt(
    "Validate ticket {ticketId} end to end. Inspect implementation below. Run focused automated tests, then perform a full agent-browser UI run against the client Odoo instance: open the real URL, reproduce the original path, exercise the fixed behavior, and capture any console/page/network failures. Do not skip browser validation. Do not mutate production data or submit irreversible actions. Report exact steps and results.\n\n{implementation}",
    { ticketId: args.ticketId, implementation },
  ),
);

const review = await agent(
  prompt(
    "Review ticket {ticketId} for correctness and completeness. Check diagnosis, implementation, automated tests, and full agent-browser validation. If validation failed, identify required fixes; otherwise confirm release readiness.\n\nDiagnosis:\n{diagnosis}\n\nImplementation:\n{implementation}\n\nValidation:\n{validation}",
    { ticketId: args.ticketId, diagnosis, implementation, validation },
  ),
);

const artifacts = await agent(
  prompt(
    "Finalize ticket {ticketId}. Commit implementation using the existing helpdesk workflow rules. Then write two Markdown artifacts exactly at /tmp/pi/hd-{ticketId}/pr-v1.md and /tmp/pi/hd-{ticketId}/commit-1-v1.md. pr-v1.md must contain PR summary, ticket, changed files, tests, full agent-browser validation steps/results, and risks. commit-1-v1.md must contain commit message, commit hash, changed files, and verification results. Do not push or create a remote PR.\n\nReview:\n{review}\n\nImplementation:\n{implementation}\n\nValidation:\n{validation}",
    { ticketId: args.ticketId, review, implementation, validation },
  ),
);

return { intake, questions, finalizedIntake, diagnosis, implementation, validation, review, artifacts };
