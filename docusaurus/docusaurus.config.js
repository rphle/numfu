/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "NumFu",
  tagline:
    "Functional programming language designed for readability, extensibility and arbitrary precision math.",
  favicon: "img/favicon.ico",

  future: {
    v4: true,
  },

  url: "https://rphle.github.io/",
  baseUrl: "/numfu",
  trailingSlash: false,

  organizationName: "rphle",
  projectName: "numfu",

  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",

  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          path: "../docs",
          sidebarPath: "./sidebars.js",
          editUrl: "https://github.com/rphle/numfu/tree/main/docs/",
        },

        theme: {
          customCss: "./src/css/theme.css",
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: "img/banner.png",
      metadata: [
        {
          name: "keywords",
          content:
            "numfu, functional programming, programming language, programming, extensible, arbitrary precision, mathematics, computation, pipes, composition",
        },
        {
          name: "description",
          content:
            "NumFu is a functional programming language designed for readability, extensibility and arbitrary precision arithmetic.",
        },
      ],
    }),
};

export default config;
