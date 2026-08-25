export default function DifficultyStars({ level }: { level: number }) {
  return (
    <span className="text-xs tracking-tight">
      {Array.from({ length: 5 }).map((_, i) => (
        <span key={i} className={i < level ? "text-accent" : "text-bg-border"}>
          ●
        </span>
      ))}
    </span>
  );
}
