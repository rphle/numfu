// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docsSidebar: [
    {
      type: "html",
      value:
        "<h1 style='font-size: 250%'><a href='/' style='text-decoration: none; color: var(--text-color)'>NumFu</a> <span style='font-weight: 300'>Docs</span></h1><hr>",
      className: "sidebar-title",
      defaultStyle: true,
    },
    {
      type: "doc",
      id: "readme",
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
        "guide/modules",
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
