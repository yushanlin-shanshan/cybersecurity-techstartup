export const reviewStatuses = {
  new: ['New', 'Waiting for review. You can reopen an event by returning it to New.'],
  investigating: ['Investigating', 'A reviewer is checking the evidence and deciding what to do.'],
  resolved: ['Resolved', 'The investigation is complete and any needed action is finished.'],
  dismissed: ['Dismissed', 'Reviewed and closed without further action, such as expected activity or a duplicate.'],
};
export const reviewAssessments = {
  unreviewed: 'Not assessed', suspicious: 'Suspicious', benign: 'Benign / expected', confirmed: 'Confirmed threat',
};
export function validateReview(value) {
  if(!value||!Object.hasOwn(reviewStatuses,value.status))throw Error('Choose a valid review status.');
  if(!Object.hasOwn(reviewAssessments,value.disposition))throw Error('Choose a valid assessment.');
  if(typeof value.note!=='string'||[...value.note].length>2000)throw Error('Review notes must be at most 2,000 characters.');
  return {status:value.status,disposition:value.disposition,note:value.note};
}
