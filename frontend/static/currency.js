function formatINR(value) {
  if (value === null || value === undefined) return "";
  return "₹" + Math.round(value).toLocaleString("en-IN");
}