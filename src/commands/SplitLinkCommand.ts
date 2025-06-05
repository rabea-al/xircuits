/*  SplitLinkCommand.ts  */
import {
  DefaultLinkModel,
  DiagramModel
} from '@projectstorm/react-diagrams';
import { Point } from '@projectstorm/geometry';
import { CustomPortModel } from '../components/port/CustomPortModel';

export class SplitLinkCommand {
  constructor(
    private diagramModel : DiagramModel,
    private draggedNode   : any,       // The node dropped by the user onto an existing link
    private linkId        : string,    // ID of the original link being split
    private dropPosition  : Point      // Coordinates of the drop location
  ) {}

  /**
   * Forcefully connects src → dst:
   * 1) Removes all existing links from both ports
   * 2) Creates a new DefaultLinkModel and adds it to the diagram
   * (Bypasses all canLinkToPort rules)
   */
  private forceLink(src: CustomPortModel, dst: CustomPortModel): void {
    // Remove existing links from both source and destination ports
    Object.values(src.getLinks()).forEach(l => this.diagramModel.removeLink(l));
    Object.values(dst.getLinks()).forEach(l => this.diagramModel.removeLink(l));

    // Create and add new link directly
    const newLink = new DefaultLinkModel();
    newLink.setSourcePort(src);
    newLink.setTargetPort(dst);
    this.diagramModel.addLink(newLink);
  }

  execute(): void {
    /* ===== 0. Retrieve the original link ===== */
    const oldLink = this.diagramModel.getLink(this.linkId) as DefaultLinkModel;
    if (!oldLink) return;

    const srcPort = oldLink.getSourcePort() as CustomPortModel;
    const dstPort = oldLink.getTargetPort() as CustomPortModel;
    if (!srcPort || !dstPort) return;

    /* ===== 1. Add the dragged node if it's not already on the canvas ===== */
    if (!this.diagramModel.getNode(this.draggedNode.getID())) {
      this.diagramModel.addNode(this.draggedNode);
    }

    // Position the node at the drop location
    this.draggedNode.setPosition(this.dropPosition.x, this.dropPosition.y);

    /* ===== 2. Get in-0 and out-0 ports from the dropped node ===== */
    const inPort  = this.draggedNode.getPort('in-0')  as CustomPortModel;
    const outPort = this.draggedNode.getPort('out-0') as CustomPortModel;
    if (!inPort || !outPort) {
      console.warn('[SplitLink] Dropped node is missing in-0 or out-0 ports.');
      return;
    }

    /* ===== 3. Remove the original link completely ===== */
    this.diagramModel.removeLink(oldLink);

    /* ===== 4. Remove existing links from all involved ports ===== */
    Object.values(srcPort.getLinks()).forEach(l => this.diagramModel.removeLink(l));
    Object.values(inPort.getLinks()).forEach(l => this.diagramModel.removeLink(l));
    Object.values(dstPort.getLinks()).forEach(l => this.diagramModel.removeLink(l));

    /* ===== 5. Create two new links unconditionally ===== */
    this.forceLink(srcPort, inPort);   // Original source → new node
    this.forceLink(outPort, dstPort);  // New node → original target
  }
}
