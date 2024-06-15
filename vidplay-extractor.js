import fs from 'fs';
import { webcrack } from 'webcrack';

function getCodeVersion() {
    const versionDate = new Date();
    versionDate.setMinutes(0);
    versionDate.setSeconds(10);
    const timestamp = versionDate.getTime().toString().substring(0, 10);
    return parseInt(timestamp).toString(16);
}

async function extractKeys() {
    const response = await fetch(`https://vidplay.online/assets/mcloud/min/embed.js?v=${getCodeVersion()}`);
    let data = await response.text();
    for (let i = 0; i < 3; i++) {
        data = (await webcrack(data)).code;
    }

    const start = data.substring(data.indexOf('loading()'));
    const end = start.substring(0, start.indexOf('function'));
    const variables = end.match(/loading\(\);\s*var\s.\s=\s.\(([^,]+),\sthis\..{1}\);\s*.\s=\s.\(([^,]+),\s.{1}\);/);
    const key1Vars = variables[1].split(' + ');
    const key2Vars = variables[2].split(' + ');
    let keys = ['', ''];

    for (const keyVars of [key1Vars, key2Vars]) {
        let index = keyVars === key1Vars ? 0 : 1; 
        for (const key of keyVars) {
            const pattern = new RegExp(`${key}\\s*=\\s*"(.+?)";`, 'g');
            const segments = [...data.matchAll(pattern)];
            const lastSegment = segments[segments.length - 1]?.[1];
            if (lastSegment) {
                keys[index] += lastSegment;
            }
        }
    }

    console.log("Extracted Keys:", keys)
    fs.writeFileSync('keys.json', JSON.stringify(keys), 'utf-8')
}

extractKeys();