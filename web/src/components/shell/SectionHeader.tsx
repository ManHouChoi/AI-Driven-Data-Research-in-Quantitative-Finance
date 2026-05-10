import clsx from "clsx";

interface SectionHeaderProps {
  kicker: string;
  title: string;
  copy: string;
  align?: "left" | "center";
}

export function SectionHeader({
  kicker,
  title,
  copy,
  align = "left"
}: SectionHeaderProps) {
  return (
    <div
      className={clsx(
        "max-w-3xl",
        align === "center" && "mx-auto text-center"
      )}
    >
      <p className="mb-3 font-mono text-xs uppercase text-mercury-silver">
        {kicker}
      </p>
      <h2 className="font-display text-3xl font-normal leading-tight text-mercury-starlight sm:text-5xl">
        {title}
      </h2>
      <p className="mt-4 text-base leading-7 text-mercury-silver sm:text-lg">
        {copy}
      </p>
    </div>
  );
}
