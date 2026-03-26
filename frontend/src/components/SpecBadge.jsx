const SPEC_COLORS = {
  diego: "#71717a",
  intake: "#5599ff",
  coding: "#a78bfa",
  planning: "#fb923c",
  research: "#34d399",
};

function SpecBadge({ spec }) {
  return (
    <span
      className="spec-badge"
      style={{
        color: SPEC_COLORS[spec] || SPEC_COLORS.diego,
        borderColor: SPEC_COLORS[spec] || SPEC_COLORS.diego,
      }}
    >
      {spec}
    </span>
  );
}

export default SpecBadge;