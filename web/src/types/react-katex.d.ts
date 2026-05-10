declare module "react-katex" {
  import type { ReactNode } from "react";

  interface MathComponentProps {
    children?: string;
    errorColor?: string;
    math?: string;
    renderError?: (error: Error) => ReactNode;
  }

  export function InlineMath(props: MathComponentProps): ReactNode;
  export function BlockMath(props: MathComponentProps): ReactNode;
}
