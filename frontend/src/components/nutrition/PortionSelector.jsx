import Input from '../ui/Input';

export default function PortionSelector({ portion = 100, onChange }) {
  return (
    <div className="flex items-center gap-2 mt-2">
      <label className="text-sm text-gray-600">Porsi:</label>
      <Input
        type="number"
        value={portion}
        onChange={(e) => onChange(Number(e.target.value))}
        min="1"
        className="w-20"
      />
      <span className="text-sm text-gray-600">gram</span>
    </div>
  );
}
