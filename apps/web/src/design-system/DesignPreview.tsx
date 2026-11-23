import { Button } from "./button/Button";
import { Chip, type ChipTone } from "./chip/Chip";
import styles from "./DesignPreview.module.css";
import { IconButton } from "./icon-button/IconButton";
import { Skeleton } from "./skeleton/Skeleton";
import { Surface } from "./surface/Surface";
import { categoryAccents, chipText, colors, fontSizes, fontWeights, spacing } from "./tokens";

const typeScaleNames = ["xs", "sm", "md", "lg", "xl", "2xl", "3xl"] as const;
const chipTones: readonly ChipTone[] = [
  "neutral",
  "primary",
  "success",
  "warning",
  "danger",
  "violet",
];

/**
 * Development aid that renders every token and primitive for visual review
 * (ADR 0003 items 2 to 8 and 14). Reachable from App through the
 * "#design-preview" hash until a later part replaces it with a route.
 */
export function DesignPreview() {
  return (
    <main className={styles.preview}>
      <header className={styles.header}>
        <h1>Design preview</h1>
        <p className={styles.note}>
          Development aid for the design system. Every value below comes from the tokens in ADR
          0003. Open <code className={styles.inlineCode}>#design-preview</code> to view it.
        </p>
      </header>

      <section className={styles.section} aria-labelledby="colors-heading">
        <h2 id="colors-heading">Colors</h2>
        <ul className={styles.swatches}>
          {Object.entries(colors).map(([name, value]) => (
            <li key={name} className={styles.swatch}>
              <span
                className={styles.swatchColor}
                style={{ backgroundColor: value }}
                aria-hidden="true"
              />
              <span className={styles.swatchName}>{name}</span>
              <span className={styles.swatchValue}>{value}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.section} aria-labelledby="chip-colors-heading">
        <h2 id="chip-colors-heading">Chip text tokens</h2>
        <ul className={styles.swatches}>
          {Object.entries(chipText).map(([name, value]) => (
            <li key={name} className={styles.swatch}>
              <span
                className={styles.swatchColor}
                style={{ backgroundColor: value }}
                aria-hidden="true"
              />
              <span className={styles.swatchName}>{name}</span>
              <span className={styles.swatchValue}>{value}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.section} aria-labelledby="accents-heading">
        <h2 id="accents-heading">Category accents</h2>
        <ul className={styles.swatches}>
          {Object.entries(categoryAccents).map(([name, value]) => (
            <li key={name} className={styles.swatch}>
              <span
                className={styles.swatchColor}
                style={{ backgroundColor: value }}
                aria-hidden="true"
              />
              <span className={styles.swatchName}>{name}</span>
              <span className={styles.swatchValue}>{value}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.section} aria-labelledby="type-heading">
        <h2 id="type-heading">Type scale</h2>
        <div className={styles.scale}>
          {fontSizes.map((size, index) => (
            <div key={size} className={styles.scaleRow}>
              <span className={styles.scaleLabel}>
                {typeScaleNames[index] ?? index} / {size}px
              </span>
              <span style={{ fontSize: size }}>The quick brown fox jumps over the lazy dog</span>
            </div>
          ))}
          <div className={styles.scaleRow}>
            <span className={styles.scaleLabel}>weights</span>
            <span style={{ fontWeight: fontWeights.regular }}>Regular 400</span>
            <span style={{ fontWeight: fontWeights.medium }}>Medium 500</span>
            <span style={{ fontWeight: fontWeights.semibold }}>Semibold 600</span>
          </div>
        </div>
      </section>

      <section className={styles.section} aria-labelledby="spacing-heading">
        <h2 id="spacing-heading">Spacing scale</h2>
        <div className={styles.scale}>
          {spacing.map((size, index) => (
            <div key={size} className={styles.spacingRow}>
              <span className={styles.scaleLabel}>
                space-{index + 1} / {size}px
              </span>
              <span className={styles.spacingBar} style={{ width: size * 3 }} aria-hidden="true" />
            </div>
          ))}
        </div>
      </section>

      <section className={styles.section} aria-labelledby="buttons-heading">
        <h2 id="buttons-heading">Buttons</h2>
        <div className={styles.buttonRow}>
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Danger</Button>
        </div>
        <div className={styles.buttonRow}>
          <Button size="lg">Large primary</Button>
          <Button size="lg" variant="secondary">
            Large secondary
          </Button>
        </div>
        <div className={styles.buttonRow}>
          <Button disabled>Disabled</Button>
          <Button loading>Loading</Button>
          <IconButton label="Add task">+</IconButton>
          <IconButton label="Close" disabled>
            ×
          </IconButton>
        </div>
      </section>

      <section className={styles.section} aria-labelledby="surfaces-heading">
        <h2 id="surfaces-heading">Surfaces</h2>
        <div className={styles.surfaceRow}>
          <Surface elevation="flat">
            <div className={styles.surfaceContent}>
              <h3>Flat surface</h3>
              <p className={styles.muted}>Opaque surface color with the panel radius.</p>
            </div>
          </Surface>
          <Surface elevation="floating">
            <div className={styles.surfaceContent}>
              <h3>Floating surface</h3>
              <p className={styles.muted}>
                Surface at 80 percent with a 12 px blur and the floating shadow.
              </p>
            </div>
          </Surface>
        </div>
      </section>

      <section className={styles.section} aria-labelledby="chips-heading">
        <h2 id="chips-heading">Chips</h2>
        <div className={styles.chipRow}>
          {chipTones.map((tone) => (
            <Chip key={tone} tone={tone}>
              {tone}
            </Chip>
          ))}
          <Chip tone="danger" icon="!">
            Overdue
          </Chip>
          <Chip tone="primary" icon="→">
            In progress
          </Chip>
        </div>
      </section>

      <section className={styles.section} aria-labelledby="loading-heading">
        <h2 id="loading-heading">Loading</h2>
        <Skeleton height={16} />
        <Skeleton width="60%" height={16} />
        <Skeleton width={120} height={40} />
      </section>

      <section className={styles.section} aria-labelledby="focus-heading">
        <h2 id="focus-heading">Focus ring</h2>
        <div className={styles.focusDemo}>
          <Button variant="secondary">Tab to me for the focus ring</Button>
          <a href="#design-preview">Focusable link</a>
        </div>
      </section>

      <section className={styles.section} aria-labelledby="user-text-heading">
        <h2 id="user-text-heading">User text direction</h2>
        <div className={styles.userText}>
          <p className="user-text" dir="auto" lang="ar">
            اكتب تقرير المشروع
          </p>
          <p className="user-text" dir="auto" lang="en">
            Write the project report
          </p>
        </div>
      </section>
    </main>
  );
}
