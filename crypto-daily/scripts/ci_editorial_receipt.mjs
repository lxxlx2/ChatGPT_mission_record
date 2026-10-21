import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { validateEditorial } from './editorial_gate.mjs';

const repo=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const rulesPath='crypto-daily/EDITORIAL_RULESET.json';
const gatePath='crypto-daily/scripts/editorial_gate.mjs';
const file=String(process.argv[2]||'');
if(!/^crypto-daily\/delivery-pending\/20\d\d-\d\d-\d\d\.json$/.test(file))throw Error('INVALID_PENDING_FILE_NAME');
const filename=path.resolve(repo,file);
if(!filename.startsWith(path.resolve(repo,'crypto-daily/delivery-pending')+path.sep))throw Error('UNSAFE_PATH');
const manifest=JSON.parse(fs.readFileSync(filename,'utf8'));
const rules=JSON.parse(fs.readFileSync(path.resolve(repo,rulesPath),'utf8'));
const result=validateEditorial(manifest,rules);
if(!result.passed){
  process.stderr.write(JSON.stringify({state:'QA_FAIL_NO_SEND',path:file,...result},null,2)+'\n');
  process.exit(1);
}
const sha=p=>execFileSync('git',['hash-object',p],{cwd:repo,encoding:'utf8'}).trim();
const date=path.basename(file,'.json');
if(manifest.report_date!==date)throw Error('REPORT_DATE_MISMATCH');
const output={
  schema:'CRYPTO_DAILY_EDITORIAL_CI_RECEIPT_V1',
  report_date:date,manifest_path:file,
  manifest_blob_sha:sha(file),rules_blob_sha:sha(rulesPath),
  editorial_gate_blob_sha:sha(gatePath),git_trigger_commit:process.env.GITHUB_SHA||'UNVERIFIED',
  status:'EDITORIAL_QA_PASS',validated_at:new Date().toISOString(),
  metrics:result.metrics,warnings:result.warnings,
  scope_note:'Checks classification, declared original-source receipts, text/metadata consistency, known event versions and minimum market evidence. It does NOT independently confirm external news freshness, all source recall or Gmail delivery.'
};
const outDir=path.resolve(repo,'crypto-daily/delivery-qa');
fs.mkdirSync(outDir,{recursive:true});
fs.writeFileSync(path.join(outDir,date+'.json'),JSON.stringify(output,null,2)+'\n','utf8');
process.stdout.write(JSON.stringify({status:output.status,report_date:date,manifest_sha:output.manifest_blob_sha,rules_sha:output.rules_blob_sha})+'\n');
