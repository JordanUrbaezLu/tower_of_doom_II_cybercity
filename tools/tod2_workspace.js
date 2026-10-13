const fs = require('fs'), path = require('path');
const ROOT = 'C:/BO3Tools/TOD2Cybercity';
function toolsRoot(override = '') {
    if (override && path.resolve(override).toLowerCase() !== path.resolve(ROOT).toLowerCase())
        throw Error('TOD II isolation: shared tools root overrides are forbidden.');
    const owner = JSON.parse(fs.readFileSync(path.join(ROOT, '.tod2-workspace.json'), 'utf8').replace(/^\uFEFF/, ''));
    if (owner.map !== 'zm_tod2_cybercity' || path.resolve(owner.repository).toLowerCase() !== path.resolve(__dirname, '..').toLowerCase())
        throw Error('TOD II isolation: workspace belongs to another map/repository.');
    return ROOT;
}
function assertWrite(file, repository = false) {
    const full = path.resolve(file), base = (repository ? path.resolve(__dirname, '..') : path.resolve(toolsRoot())).toLowerCase() + path.sep;
    if (!full.toLowerCase().startsWith(base)) throw Error('TOD II isolation: write outside private root: ' + file);
    for (let cursor = full; cursor !== path.dirname(cursor); cursor = path.dirname(cursor)) {
        if (fs.existsSync(cursor) && fs.lstatSync(cursor).isSymbolicLink())
            throw Error('TOD II isolation: cannot edit a stock-source junction: ' + cursor);
    }
}
module.exports = {toolsRoot, assertWrite};
