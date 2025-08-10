// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docsSidebar: [
    {
      type: "doc",
      id: "index",
      label: "Getting Started",
    },
    {
      type: "category",
      label: "Guide",
      collapsed: false,
      items: [
        "guide/basic-syntax",
        "guide/arithmetic",
        "guide/booleans",
        "guide/variables",
        "guide/functions",
        "guide/lists",
        "guide/strings",
        "guide/operators",
        "guide/partial-application",
        "guide/printing",
      ],
    },
    {
      type: "category",
      label: "Reference",
      collapsed: false,
      items: ["reference/builtins", "reference/cli"],
    },
  ],
};

export default sidebars;
