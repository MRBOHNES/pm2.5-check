const LINKS = [
  { href: "https://open-meteo.com/en/docs/air-quality-api", label: "Open-Meteo Air Quality API (modelled)" },
  { href: "https://docs.openaq.org", label: "OpenAQ API (measured)" },
  { href: "https://cpcb.nic.in/national-air-quality-index/", label: "CPCB National AQI" },
  { href: "https://leap.unep.org/akn/in/act/2009/b-29016-20-90-pci-l/eng@2009-11-18", label: "India's 2009 air quality standards (60 µg/m³, 24-hour PM2.5)" },
  { href: "https://github.com/MRBOHNES/pm2.5-check", label: "Source code on GitHub" },
];

/** What the numbers can and can't tell you, with links to every source. */
export function Limitations({ apiUrl }: { apiUrl: string }) {
  return (
    <section className="section" aria-labelledby="limits-title">
      <div className="container">
        <div className="section__head">
          <h2 className="h2" id="limits-title">Limitations</h2>
        </div>
        <div className="card limits">
          <ul className="bullets">
            <li><strong>Modelled is not measured.</strong> Open-Meteo values come from the CAMS global model on a grid cell of about
              45 km; stations read at a point. Part of any gap is that mismatch, not model error.</li>
            <li><strong>Few stations, Delhi only.</strong> Measured data is the mean of five hand-picked Delhi stations, not a full
              network. Other cities show modelled values only.</li>
            <li><strong>A short window.</strong> Thirty days is too few to say how the model behaves across seasons. Days with fewer
              than 18 valid hourly readings have no daily value.</li>
            <li><strong>The standard is a reference line.</strong> 60 µg/m³ is India&apos;s 24-hour limit, and it also happens to be
              the top of CPCB&apos;s &ldquo;Satisfactory&rdquo; band. CPCB&apos;s official label for 61–90 is &ldquo;Moderately polluted&rdquo;.</li>
          </ul>
          <ul className="links">
            {LINKS.map((l) => (
              <li key={l.href}><a href={l.href} target="_blank" rel="noreferrer">{l.label}</a></li>
            ))}
            <li><a href={`${apiUrl}/docs`} target="_blank" rel="noreferrer">API documentation (/docs)</a></li>
          </ul>
        </div>
      </div>
    </section>
  );
}
