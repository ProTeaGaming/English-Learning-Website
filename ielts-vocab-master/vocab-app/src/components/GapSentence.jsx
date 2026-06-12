export default function GapSentence({ gap }) {
  const parts = gap.split("___");
  return (
    <>
      {parts[0]}
      <span className="gapblank">_____</span>
      {parts[1]}
    </>
  );
}
