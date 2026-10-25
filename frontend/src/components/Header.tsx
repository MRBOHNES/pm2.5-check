import type { City } from "../types";

interface Props {
  cities: City[];
  city: string;
  onCity: (name: string) => void;
}

/** Site title, tagline and the city picker (only cities the backend supports). */
export function Header({ cities, city, onCity }: Props) {
  return (
    <header className="header">
      <div className="container header__inner">
        <div>
          <p className="header__title">PM2.5 Check</p>
          <p className="header__tagline small">Modelled vs measured PM2.5 in Delhi</p>
        </div>
        <label className="city-picker">
          <span className="small muted">City</span>
          <select value={city} onChange={(e) => onCity(e.target.value)} disabled={cities.length === 0}>
            {cities.map((c) => (
              <option key={c.name} value={c.name}>{c.label}</option>
            ))}
          </select>
        </label>
      </div>
    </header>
  );
}
