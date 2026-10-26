import { toCsv } from "./csv";

describe("toCsv", () => {
  it("escapes quotes, commas and blanks", () => {
    expect(
      toCsv(
        ["a", "b"],
        [
          [1, null],
          ['x,"y"', 2],
        ],
      ),
    ).toBe('a,b\n1,\n"x,""y""",2');
  });
});
