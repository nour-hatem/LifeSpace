import { DesignPreview } from "./design-system/DesignPreview";
import { ApiStatus } from "./features/system-status/ApiStatus";

/**
 * Root view. The design preview is a temporary hash switch (ADR 0003 items 2
 * to 8) that a later M3 part replaces with a real route.
 */
export function App() {
  if (window.location.hash === "#design-preview") {
    return <DesignPreview />;
  }

  return (
    <main>
      <h1>LifeSpace</h1>
      <ApiStatus />
    </main>
  );
}
