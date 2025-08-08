import clsx from "clsx";
import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Layout from "@theme/Layout";
import Heading from "@theme/Heading";
import CodeBlock from "@theme/CodeBlock";
import styles from "./index.module.css";

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className={clsx("hero", styles.heroMinimal)}>
      <div className="container text--center">
        <Heading as="h1" className="hero__title">
          <strong>NumFu</strong>
        </Heading>
        <p className="hero__subtitle">
          A functional programming language designed for readability,
          extensibility and math.
        </p>
        <div className="buttons">
          <Link className="button button--primary button--lg" to="/docs/">
            Get started →
          </Link>
          <Link
            className="button button--outline button--lg margin-left--sm"
            to="https://github.com/dr-lego/numfu"
          >
            GitHub
          </Link>
          <Link
            className="button button--outline button--lg margin-left--sm"
            to="https://pypi.org/project/numfu-lang/"
          >
            PyPI
          </Link>
        </div>
      </div>
    </header>
  );
}

function QuickstartSection() {
  const example = `// Approximate the golden ratio
let golden = {depth ->
  let recur =
    {d -> if d <= 0 then 1 else 1 + 1 / recur(d - 1)}
  in recur(depth)
} in golden(10) // ≈ 1.618

// Composition and pipes
let add1 = {x -> x + 1},
    double = {x -> x * 2}
in 5 |> (add1 >> double) // 12

// Assertions
sqrt(49) ---> _ == 7`;

  return (
    <section className="margin-bottom--lg">
      <div className="container">
        <Heading as="h2" className="text--center margin-bottom--md">
          Quickstart
        </Heading>
        <div className={`row equal-height`}>
          <div className="col col--6">
            <CodeBlock language="numfu" title="Code Example">
              {example}
            </CodeBlock>
          </div>
          <div className="col col--6">
            <CodeBlock language="bash" title="Install from PyPI">
              pip install numfu-lang
            </CodeBlock>
            <CodeBlock language="bash" title="Start an interactive REPL">
              numfu repl
            </CodeBlock>
            <CodeBlock language="bash" title="Run a file">
              numfu example.nfu
            </CodeBlock>
          </div>
        </div>
      </div>
    </section>
  );
}

function IdeasSection() {
  return (
    <section className="margin-bottom--xl">
      <div className="container">
        <Heading as="h2" className="text--center margin-bottom--lg">
          What Makes NumFu Special?
        </Heading>
        <div className="row">
          <div className="col col--6 margin-top--lg">
            <ul className="feature-list">
              <li>
                <strong>Functions First:</strong> Everything is a function. You
                can curry, compose, and pass functions freely; partial
                application is natively supported.
              </li>
              <li>
                <strong>Clean Syntax:</strong> Intuitive syntax inspired by
                math, designed to be readable even for those who don’t use
                functional languages daily.
              </li>
              <li>
                <strong>Customizable Precision:</strong> Numbers use arbitrary
                precision by default, powered by native GNU MPFR bindings.
              </li>
              <li>
                <strong>Designed for Learning & Extensibility:</strong> NumFu is
                minimal by design, making it easy to explore, understand, and
                modify. It is 100% written in Python.
              </li>
            </ul>
          </div>
          <div className="col col--6">
            <CodeBlock language="numfu" title="A quick demo">
              {`{x, y, z -> x + y + z}(1, 2)
// {z -> 1+2+z}

{
  distance: x1, y1, x2, y2 ->
    let dx = x2 - x1, dy = y2 - y1 in
      sqrt(dx^2 + dy^2)
}
distance(0, 0, 3, 4) // 5

0.1 + 0.2 == 0.3
// true`}
            </CodeBlock>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} Programming Language`}
      description="NumFu is a minimalist functional programming language designed for readability, extensibility and math."
    >
      <HomepageHeader />
      <main>
        <QuickstartSection />
        <IdeasSection />
      </main>
    </Layout>
  );
}
