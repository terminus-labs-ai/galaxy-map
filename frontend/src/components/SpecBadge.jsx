import { SPEC_COLORS } from "../utils/helpers";

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